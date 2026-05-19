"""
Camada de LLM usando o SDK oficial do Groq.
- invoke_with_db(message, history)         → chat + consulta automática ao banco
- invoke_with_context(message, ctx, ...)   → chat com texto de arquivo
- invoke_with_image(message, bytes, ...)   → chat com imagem (Groq Vision)
- generate_title(message)                  → título curto para a conversa
"""
from __future__ import annotations

import base64
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_SYSTEM = (
    "Você é o UCBvet, assistente inteligente da equipe de vendas de uma empresa especializada "
    "em protocolos de inseminação artificial bovina (gado de corte e leite). "
    "Seu papel é auxiliar vendedores e técnicos a: consultar dados analíticos de clientes, "
    "identificar oportunidades de venda, interpretar resultados técnicos de inseminação "
    "(taxa de prenhez, ECC, ciclicidade, protocolos) e fornecer recomendações baseadas nos "
    "dados históricos da empresa. "
    "Responda sempre em português brasileiro. Seja objetivo, direto e focado em gerar valor "
    "para o vendedor em campo."
)

_MAX_CONTEXT_CHARS = 14_000
_MAX_HISTORY       = 10        # últimas N mensagens do histórico enviadas ao LLM
_MODEL_TEXT        = "llama-3.3-70b-versatile"
_MODEL_VISION      = "llama-3.2-11b-vision-preview"

_client = Groq(api_key=os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_API_KEY"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _chat(messages: list, model: str = _MODEL_TEXT) -> str:
    response = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def _stream_chat(messages: list, model: str = _MODEL_TEXT):
    """Gera chunks de texto via streaming do Groq."""
    stream = _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
        stream=True,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def _build(system: str, history: list, user_content) -> list:
    """Monta a lista de mensagens: [system] + histórico + [user atual]."""
    msgs = [{"role": "system", "content": system}]
    for h in history[-_MAX_HISTORY:]:
        msgs.append(h)
    msgs.append({"role": "user", "content": user_content})
    return msgs


# ── Funções públicas ──────────────────────────────────────────────────────────

def invoke_with_db(message: str, history: list | None = None) -> str:
    """Responde consultando o banco de dados quando a pergunta exigir dados."""
    from .db_query import SCHEMA_DESCRIPTION, execute_query
    history = history or []

    sql_system = (
        f"{_SYSTEM}\n\n"
        "Você também tem acesso a um banco de dados SQLite com dados da empresa.\n"
        f"Schema:\n{SCHEMA_DESCRIPTION}\n\n"
        "REGRAS PARA GERAR SQL:\n"
        "1. Se a pergunta precisar de dados do banco, responda SOMENTE com um bloco ```sql ... ```. "
        "Nenhuma palavra fora do bloco.\n"
        "2. Se a pergunta NÃO precisar do banco (conceitos técnicos, explicações), responda normalmente.\n"
        "3. Use SQLite válido: nunca misture colunas não-agrupadas com agregações sem GROUP BY.\n"
        "4. Para listar registros, use SELECT simples sem COUNT; para contar, use SELECT COUNT(*) separado.\n"
        "5. Se precisar de contagem E lista, prefira listar todos os registros.\n"
        "6. Sempre use LIMIT 200 no máximo.\n"
        "7. Use JOIN quando precisar de nomes de outras tabelas.\n"
        "8. Use o histórico da conversa para resolver referências como 'essa fazenda', 'esse vendedor', etc."
    )

    try:
        step1 = _chat(_build(sql_system, history, message))
    except Exception as exc:
        return f"Erro ao processar mensagem: {exc}"

    sql_match = re.search(r'```sql\s*(.*?)\s*```', step1, re.DOTALL | re.IGNORECASE)

    if not sql_match:
        return step1

    from .db_query import execute_query
    sql   = sql_match.group(1).strip()
    dados = execute_query(sql)

    resposta_system = (
        f"{_SYSTEM}\n\n"
        "Você recebeu resultados de uma consulta ao banco de dados. "
        "Responda à pergunta do usuário de forma clara e objetiva, "
        "usando os dados fornecidos. Formate bem (listas, tabelas markdown se necessário)."
    )

    prompt_final = (
        f"Pergunta: {message}\n\n"
        f"Dados consultados:\n```\n{dados}\n```\n\n"
        "Responda com base nesses dados."
    )

    try:
        return _chat(_build(resposta_system, history, prompt_final))
    except Exception as exc:
        return f"Erro ao gerar resposta: {exc}"


def invoke_with_context(message: str, file_context: str, filename: str = "",
                        history: list | None = None) -> str:
    """Resposta com base no conteúdo extraído de um arquivo."""
    history = history or []
    try:
        ctx        = file_context[:_MAX_CONTEXT_CHARS]
        truncated  = len(file_context) > _MAX_CONTEXT_CHARS
        file_note  = f'arquivo "{filename}"' if filename else "arquivo enviado"
        trunc_note = "\n\n*(conteúdo truncado por ser muito longo)*" if truncated else ""

        prompt = (
            f"O usuário enviou o {file_note} com o seguinte conteúdo:\n\n"
            f"---\n{ctx}{trunc_note}\n---\n\n"
            f"Pergunta do usuário: {message or 'Resuma e analise o conteúdo acima.'}"
        )

        return _chat(_build(_SYSTEM, history, prompt))
    except Exception as exc:
        return f"Erro ao processar arquivo: {exc}"


def invoke_with_image(message: str, image_bytes: bytes, mime_type: str,
                      filename: str = "", history: list | None = None) -> str:
    """Analisa uma imagem usando Groq Vision."""
    history = history or []
    try:
        b64  = base64.b64encode(image_bytes).decode("utf-8")
        text = message or "Descreva e analise esta imagem em detalhes."

        user_content = [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
        ]

        return _chat(_build(_SYSTEM, history, user_content), model=_MODEL_VISION)
    except Exception as exc:
        return f"Erro ao processar imagem: {exc}"


def stream_invoke_with_db(message: str, history: list | None = None):
    """Generator que faz streaming da resposta com consulta ao banco quando necessário."""
    from .db_query import SCHEMA_DESCRIPTION, execute_query
    history = history or []

    sql_system = (
        f"{_SYSTEM}\n\n"
        "Você também tem acesso a um banco de dados SQLite com dados da empresa.\n"
        f"Schema:\n{SCHEMA_DESCRIPTION}\n\n"
        "REGRAS:\n"
        "1. Se precisar de dados do banco, responda SOMENTE com ```sql ... ```. Nada mais.\n"
        "2. Se não precisar do banco, responda normalmente.\n"
        "3. Nunca misture colunas não-agrupadas com agregações sem GROUP BY.\n"
        "4. Para listar, use SELECT simples; para contar, use COUNT separado.\n"
        "5. LIMIT 200 máximo. Use JOIN para nomes de outras tabelas.\n"
        "6. Use o histórico para resolver referências como 'essa fazenda', 'esse vendedor'."
    )

    # Step 1: detectar SQL (não-streaming, rápido)
    step1 = _chat(_build(sql_system, history, message))
    sql_match = re.search(r'```sql\s*(.*?)\s*```', step1, re.DOTALL | re.IGNORECASE)

    if not sql_match:
        # Sem SQL: faz streaming da resposta direta
        yield from _stream_chat(_build(sql_system, history, message))
        return

    # Com SQL: executa query e faz streaming da resposta final
    from .db_query import execute_query, _fix_sql
    sql   = _fix_sql(sql_match.group(1).strip())
    dados = execute_query(sql)

    resposta_system = (
        f"{_SYSTEM}\n\n"
        "Você recebeu resultados de uma consulta ao banco de dados. "
        "Responda de forma clara e objetiva, usando os dados. "
        "Formate bem (listas, tabelas markdown se necessário)."
    )
    prompt_final = (
        f"Pergunta: {message}\n\n"
        f"Dados consultados:\n```\n{dados}\n```\n\n"
        "Responda com base nesses dados."
    )
    yield from _stream_chat(_build(resposta_system, history, prompt_final))


def stream_invoke_with_context(message: str, file_context: str, filename: str = "",
                                history: list | None = None):
    """Generator streaming para resposta baseada em arquivo de texto."""
    history = history or []
    ctx        = file_context[:_MAX_CONTEXT_CHARS]
    truncated  = len(file_context) > _MAX_CONTEXT_CHARS
    file_note  = f'arquivo "{filename}"' if filename else "arquivo enviado"
    trunc_note = "\n\n*(conteúdo truncado)*" if truncated else ""
    prompt = (
        f"O usuário enviou o {file_note} com o seguinte conteúdo:\n\n"
        f"---\n{ctx}{trunc_note}\n---\n\n"
        f"Pergunta: {message or 'Resuma e analise o conteúdo acima.'}"
    )
    yield from _stream_chat(_build(_SYSTEM, history, prompt))


def stream_invoke_with_image(message: str, image_bytes: bytes, mime_type: str,
                              filename: str = "", history: list | None = None):
    """Generator streaming para análise de imagem."""
    history  = history or []
    b64      = base64.b64encode(image_bytes).decode("utf-8")
    text     = message or "Descreva e analise esta imagem em detalhes."
    user_content = [
        {"type": "text", "text": text},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
    ]
    yield from _stream_chat(_build(_SYSTEM, history, user_content), model=_MODEL_VISION)


def generate_title(message: str) -> str:
    """Gera um título curto (máx 6 palavras) para a conversa a partir da primeira mensagem."""
    try:
        prompt = (
            f"Crie um título curto e descritivo (máximo 6 palavras, sem pontuação no final) "
            f"para uma conversa que começa com: \"{message[:200]}\"\n"
            "Responda APENAS com o título, sem aspas, sem explicações."
        )
        title = _chat([
            {"role": "system", "content": "Você cria títulos curtos e descritivos para conversas."},
            {"role": "user",   "content": prompt},
        ])
        return title.strip().strip('"').strip("'")[:60]
    except Exception:
        return "Nova Conversa"


# Alias para compatibilidade
invoke        = invoke_with_db
invoke_chain  = invoke_with_db
