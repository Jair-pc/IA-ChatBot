import json
from datetime import datetime

from flask import Blueprint, request, jsonify, render_template, Response, stream_with_context
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from .user import Usuario, Chat, Message
from .database import db
from .llm import (invoke_with_db, invoke_with_context, invoke_with_image, generate_title,
                  stream_invoke_with_db, stream_invoke_with_context, stream_invoke_with_image)
from .file import (
    extract_text, is_image, get_mime_type, get_extension,
    ALL_EXTENSIONS, IMAGE_EXTENSIONS, FILE_ICONS,
)

login_routes     = Blueprint("login_routes",     __name__)
index_routes     = Blueprint("index_routes",     __name__)
cadastrar_routes = Blueprint("cadastrar_routes", __name__)


# ── Auth ──────────────────────────────────────────────────────────────────────

@login_routes.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    usuario = Usuario.query.filter_by(username=dados.get("username")).first()
    if usuario and check_password_hash(usuario.password, dados.get("password", "")):
        login_user(usuario)
        return jsonify({"mensagem": "Login realizado com sucesso!"})
    return jsonify({"mensagem": "Usuário ou senha incorretos!"}), 401


@cadastrar_routes.route("/cadastrar", methods=["POST"])
def cadastrar():
    dados = request.get_json()
    nome  = dados.get("username", "").strip()
    senha = dados.get("password", "").strip()

    if not nome or not senha:
        return jsonify({"erro": "Usuário e senha são obrigatórios!"}), 400
    if Usuario.query.filter_by(username=nome).first():
        return jsonify({"erro": "Nome de usuário já existe!"}), 400

    db.session.add(Usuario(username=nome, password=generate_password_hash(senha)))
    db.session.commit()
    return jsonify({"mensagem": "Usuário cadastrado com sucesso!"})


# ── Pages ─────────────────────────────────────────────────────────────────────

@index_routes.route("/")
def index():
    return render_template("login.html")


@index_routes.route("/cadastro")
def cadastro_page():
    return render_template("cadastro.html")


@index_routes.route("/home")
@login_required
def home():
    return render_template("index.html", username=current_user.nome_usuario)


@index_routes.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("login.html")


# ── Conversations ─────────────────────────────────────────────────────────────

@index_routes.route("/get_conversations")
@login_required
def get_conversations():
    chats = (Chat.query
             .filter_by(user_id=current_user.id)
             .order_by(Chat.created_at.desc())
             .all())
    return jsonify([c.to_dict() for c in chats])


@index_routes.route("/add_chat", methods=["POST"])
@login_required
def add_chat():
    data  = request.get_json(silent=True) or {}
    title = data.get("title", "Nova Conversa")
    chat  = Chat(title=title, user_id=current_user.id)
    db.session.add(chat)
    db.session.commit()
    return jsonify({"chat_id": chat.id, "title": chat.title})


@index_routes.route("/delete_chat/<int:chat_id>", methods=["POST"])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    db.session.delete(chat)
    db.session.commit()
    return jsonify({"message": "Chat deletado."})


@index_routes.route("/update_chat_title/<int:chat_id>", methods=["POST"])
@login_required
def update_chat_title(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}
    chat.title = data.get("title", chat.title)
    db.session.commit()
    return jsonify({"message": "Título atualizado."})


# ── Messages ──────────────────────────────────────────────────────────────────

@index_routes.route("/get_messages/<int:chat_id>")
@login_required
def get_messages(chat_id):
    Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    msgs = Message.query.filter_by(chat_id=chat_id).order_by(Message.id).all()
    return jsonify([m.to_dict() for m in msgs])


@index_routes.route("/get_response/<int:chat_id>", methods=["POST"])
@login_required
def get_response(chat_id):
    """Aceita JSON puro (texto) ou multipart/form-data (texto + arquivo)."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()

    # ── Histórico da conversa para memória do LLM ─────────────────
    history_msgs = (Message.query
                    .filter_by(chat_id=chat_id)
                    .order_by(Message.id.asc())
                    .all())
    history = []
    for m in history_msgs:
        history.append({"role": "user",      "content": m.text_usuario})
        history.append({"role": "assistant", "content": m.text_servidor})

    is_first_message = len(history_msgs) == 0

    uploaded = request.files.get("file")

    if uploaded and uploaded.filename:
        # ── Mensagem com arquivo ──────────────────────────────────
        mensagem  = (request.form.get("message") or "").strip()
        filename  = secure_filename(uploaded.filename)
        ext       = get_extension(filename)

        if ext not in ALL_EXTENSIONS:
            return jsonify({"error": f"Tipo .{ext} não suportado."}), 400

        file_bytes = uploaded.read()
        icon = FILE_ICONS.get(ext, "📎")

        if is_image(ext):
            mime = get_mime_type(ext)
            resposta = invoke_with_image(mensagem, file_bytes, mime, filename, history)
            label_usuario = f"{icon} {filename}" + (f"\n{mensagem}" if mensagem else "")
        else:
            context = extract_text(file_bytes, ext)
            resposta = invoke_with_context(mensagem, context, filename, history)
            label_usuario = f"{icon} {filename}" + (f"\n{mensagem}" if mensagem else "")
    else:
        # ── Mensagem de texto simples ─────────────────────────────
        data = request.get_json(silent=True) or {}
        mensagem      = (data.get("message") or "").strip()
        label_usuario = mensagem
        if not mensagem:
            return jsonify({"error": "Mensagem vazia."}), 400
        resposta = invoke_with_db(mensagem, history)

    msg = Message(text_usuario=label_usuario, text_servidor=resposta, chat_id=chat_id)
    db.session.add(msg)

    # ── Título automático na primeira mensagem ────────────────────
    new_title = None
    if is_first_message:
        new_title = generate_title(mensagem or label_usuario)
        chat.title = new_title

    db.session.commit()

    return jsonify({"message": resposta, "new_title": new_title})


# ── Streaming ─────────────────────────────────────────────────────────────────

@index_routes.route("/stream_response/<int:chat_id>", methods=["POST"])
@login_required
def stream_response(chat_id):
    """Mesmo que get_response, mas retorna Server-Sent Events para streaming."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()

    history_msgs = (Message.query.filter_by(chat_id=chat_id)
                    .order_by(Message.id.asc()).all())
    history = []
    for m in history_msgs:
        history.append({"role": "user",      "content": m.text_usuario})
        history.append({"role": "assistant", "content": m.text_servidor})
    is_first = len(history_msgs) == 0

    uploaded = request.files.get("file")

    if uploaded and uploaded.filename:
        mensagem     = (request.form.get("message") or "").strip()
        filename     = secure_filename(uploaded.filename)
        ext          = get_extension(filename)
        if ext not in ALL_EXTENSIONS:
            return jsonify({"error": f"Tipo .{ext} não suportado."}), 400
        file_bytes   = uploaded.read()
        icon         = FILE_ICONS.get(ext, "📎")
        label_usuario = f"{icon} {filename}" + (f"\n{mensagem}" if mensagem else "")
        if is_image(ext):
            gen = stream_invoke_with_image(mensagem, file_bytes, get_mime_type(ext), filename, history)
        else:
            gen = stream_invoke_with_context(mensagem, extract_text(file_bytes, ext), filename, history)
    else:
        data          = request.get_json(silent=True) or {}
        mensagem      = (data.get("message") or "").strip()
        label_usuario = mensagem
        if not mensagem:
            return jsonify({"error": "Mensagem vazia."}), 400
        gen = stream_invoke_with_db(mensagem, history)

    chat_ref = chat

    def generate():
        full_text = ""
        try:
            for chunk in gen:
                full_text += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            return

        new_title = None
        try:
            msg = Message(text_usuario=label_usuario, text_servidor=full_text, chat_id=chat_id)
            db.session.add(msg)
            if is_first:
                new_title = generate_title(mensagem or label_usuario)
                chat_ref.title = new_title
            db.session.commit()
        except Exception:
            db.session.rollback()

        yield f"data: {json.dumps({'done': True, 'new_title': new_title})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Troca de senha ────────────────────────────────────────────────────────────

@index_routes.route("/change_password", methods=["POST"])
@login_required
def change_password():
    data        = request.get_json(silent=True) or {}
    senha_atual = data.get("current_password", "")
    nova_senha  = data.get("new_password", "").strip()

    if not check_password_hash(current_user.password, senha_atual):
        return jsonify({"error": "Senha atual incorreta."}), 400
    if len(nova_senha) < 4:
        return jsonify({"error": "Nova senha deve ter pelo menos 4 caracteres."}), 400

    current_user.password = generate_password_hash(nova_senha)
    db.session.commit()
    return jsonify({"message": "Senha alterada com sucesso!"})


# ── Exportar conversa ─────────────────────────────────────────────────────────

@index_routes.route("/export_chat/<int:chat_id>")
@login_required
def export_chat(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    msgs = Message.query.filter_by(chat_id=chat_id).order_by(Message.id).all()

    lines = [
        f"# {chat.title}\n",
        f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n",
        f"Usuário: {current_user.username}\n\n",
        "---\n\n",
    ]
    for m in msgs:
        lines.append(f"**Você:** {m.text_usuario}\n\n")
        lines.append(f"**UCBvet:** {m.text_servidor}\n\n")
        lines.append("---\n\n")

    filename = f"{chat.title.replace(' ', '_')[:40]}.md"
    return Response(
        "".join(lines),
        mimetype="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
