from flask import Blueprint, request, jsonify, render_template
from flask_login import login_user, login_required, logout_user, current_user
from .db import mysql
from .user import User
from gemini import get_gemini_response
from backend.funcoes import processar_funcoes, processar_consulta_generica

login_routes = Blueprint('login_routes', __name__)
index_routes = Blueprint('index_routes', __name__)
cadastrar_routes = Blueprint('cadastrar_routes', __name__)

# Rota para fazer login
@login_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        user = User(user_id=user_data[0], username=user_data[1])
        login_user(user)
        return jsonify({'message': 'Login realizado com sucesso!'})
    else:
        return jsonify({'error': 'Nome de usuário ou senha incorretos!'}), 401

# Rota para cadastrar um usuário
@cadastrar_routes.route('/cadastrar', methods=['POST'])
def cadastrar():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        return jsonify({'error': 'Nome de usuário já existe!'}), 400

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Usuário cadastrado com sucesso!'})

# Rota do cadastro
@cadastrar_routes.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

# Rota Inicial
@index_routes.route('/')
def index():
    return render_template('login.html')

# Rota para fazer logout
@index_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('login.html')

# Rota da home
@index_routes.route('/home')
@login_required
def home():
    username = current_user.username
    user_chats = User.get_user_chats(current_user.id)
    return render_template('index.html', username=username, user_chats=user_chats)

# Rota para obter resposta do Gemini
@index_routes.route('/get_response/<int:chat_id>', methods=['POST'])
@login_required
def get_response(chat_id):
    print(f"Recebendo requisição para chat_id: {chat_id}")
    data = request.get_json()
    user_message = data.get('message')
    print(f"Mensagem do usuário: {user_message}")
    
    # Verificar se o chat_id existe na tabela chats
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM chats WHERE id = %s AND user_id = %s", (chat_id, current_user.id))
    chat = cur.fetchone()
    cur.close()
    if not chat:
        print("Chat não encontrado.")
        return jsonify({'response': 'Chat não encontrado.'}), 404

    # Consultar o banco de dados primeiro
    resposta_db = processar_funcoes(user_message)
    
    if resposta_db:
        return jsonify({'response': resposta_db})
    else:
        # Se não encontrar no banco de dados, consulta a API do Gemini
        response = get_gemini_response(user_message)
        print(f"Resposta do Gemini: {response}")
        
        if response == "Erro ao obter resposta do servidor.":
            return jsonify({'response': response}), 500
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO messages (text_usuario, text_servidor, chat_id) VALUES (%s, %s, %s)", (user_message, response, chat_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({'response': response})

# Rota para adicionar chat
@index_routes.route('/add_chat', methods=['POST'])
@login_required
def add_chat():
    data = request.get_json()
    title = data.get('title')
    user_id = current_user.id

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO chats (title, user_id) VALUES (%s, %s)", (title, user_id))
    mysql.connection.commit()

    chat_id = cur.lastrowid
    cur.close()

    print(f"Novo chat criado com ID: {chat_id}")
    return jsonify({'chat_id': chat_id, 'title': title})

# Rota para obter conversas do usuário
@index_routes.route('/get_conversations', methods=['GET'])
@login_required
def get_conversations():
    user_id = current_user.id
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, user_id FROM chats WHERE user_id = %s", (user_id,))
    chats = cur.fetchall()
    cur.close()

    formatted_chats = [{"id": chat[0], "title": chat[1], "user_id": chat[2]} for chat in chats]
    return jsonify(formatted_chats)

# Rota para obter mensagens
@index_routes.route('/get_messages/<int:chat_id>')
@login_required
def get_messages(chat_id):
    user_id = current_user.id
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM messages WHERE chat_id = %s AND EXISTS (SELECT 1 FROM chats WHERE id = %s AND user_id = %s)", (chat_id, chat_id, user_id))
    messages = cur.fetchall()
    cur.close()

    formatted_messages = [{"id": message[0], "usuario": message[1], "servidor": message[2]} for message in messages]
    return jsonify(formatted_messages)

# Rota para deletar chat
@index_routes.route('/delete_chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    user_id = current_user.id
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
        chat = cur.fetchone()
        if not chat:
            return jsonify({"error": "Chat não encontrado ou não pertence ao usuário."}), 403

        cur.execute("DELETE FROM messages WHERE chat_id = %s", (chat_id,))
        mysql.connection.commit()

        cur.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
        mysql.connection.commit()

        cur.close()
        return jsonify({"message": "Chat deletado com sucesso."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rota para atualizar o título do chat
@index_routes.route('/update_chat_title/<int:chat_id>', methods=['POST'])
@login_required
def update_chat_title(chat_id):
    user_id = current_user.id
    try:
        data = request.get_json()
        new_title = data.get('title')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM chats WHERE id = %s AND user_id = %s", (chat_id, user_id))
        chat = cur.fetchone()
        if not chat:
            return jsonify({"error": "Chat não encontrado ou não pertence ao usuário."}), 403

        cur.execute("UPDATE chats SET title = %s WHERE id = %s", (new_title, chat_id))
        mysql.connection.commit()

        cur.close()
        return jsonify({"message": "Título do chat atualizado com sucesso."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Nova rota para processar consultas SQL e funções específicas
@index_routes.route('/get_response', methods=['POST'])
@login_required
def get_response_sql():
    dados = request.get_json()
    mensagem = dados.get('mensagem')
    resposta = processar_funcoes(mensagem)
    return jsonify({'resposta': resposta})
