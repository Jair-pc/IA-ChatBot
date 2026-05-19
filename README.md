# UCBvet — Assistente Inteligente de Inseminação Bovina

Assistente web de inteligência artificial desenvolvido para **aumentar a eficácia comercial** de uma empresa especializada em protocolos de inseminação artificial para gado de corte e leite. O UCBvet conecta vendedores e técnicos a dados analíticos e técnicos da empresa por meio de linguagem natural, eliminando a necessidade de consultas manuais em planilhas ou sistemas.

---

## Objetivo do Projeto

O projeto demonstra três capacidades centrais de customização de LLMs para requisitos de negócio:

1. **Configuração do LLM para o domínio** — conta Groq, definição de perfil (persona UCBvet), chain de raciocínio, gestão de contexto e instruções de sistema específicas para veterinária e vendas.

2. **Arquitetura de dados para o LLM** — integração de dados estruturados (banco SQLite com vendas, visitas, vacas, inseminações) e não estruturados (PDFs, planilhas, imagens), com estratégia de obtenção via geração automática de SQL e extração de texto.

3. **Aprendizado corporativo contínuo** — o histórico de conversas é armazenado por usuário, criando uma base de conhecimento consultável e permitindo que o assistente evolua com os dados reais da operação.

### Contexto de negócio

A empresa possui uma base de dados técnica com eficácia de inseminação por fazenda, raça, protocolo e inseminador — um diferencial competitivo que, quando acessível pelo vendedor durante a visita, permite recomendações personalizadas e aumenta a taxa de conversão.

### Capacidades entregues

- **Acesso analítico por texto** — vendas, visitas, dados técnicos consultados em linguagem natural
- **Cálculo de potencial por cliente** — análise de histórico de fazendas e protocolos utilizados
- **Dados técnicos de fecundação** — taxa de prenhez (DG), ciclicidade, ECC e resultados por protocolo/touro
- **Suporte a documentos e imagens** — análise de laudos, fichas e planilhas enviadas pelo usuário

---

## Funcionalidades

- **Streaming de respostas** — texto gerado em tempo real, palavra por palavra (Server-Sent Events)
- **Memória de conversa** — histórico completo passado ao LLM a cada mensagem; o assistente lembra o contexto anterior
- **Consulta automática ao banco** — perguntas convertidas em SQL automaticamente (Text-to-SQL de dois passos)
- **Título automático** — nome da conversa gerado pelo LLM na primeira mensagem
- **Upload de arquivos** — PDF, TXT, DOCX, XLS/XLSX, CSV e imagens (13 formatos)
- **Exportar conversa** — download do histórico completo em Markdown (`.md`)
- **Troca de senha** — modal integrado na sidebar com validação
- **Autenticação** — login, cadastro e logout com senha criptografada (bcrypt)
- **Tema escuro/claro** — alternável, preferência salva no navegador
- **Sidebar recolhível** — histórico agrupado por Hoje / Ontem / Últimos 7 dias / Mais antigos
- **Parar geração** — botão cancela o streaming de verdade (cancela a leitura do ReadableStream)

---

## Arquitetura do Chat

```
Usuário digita mensagem
        │
        ▼
  /stream_response (SSE)
        │
        ├─► Busca histórico do chat no banco (memória)
        │
        ├─► [Texto] stream_invoke_with_db()
        │       ├─ Step 1: LLM detecta se precisa de SQL (não-streaming)
        │       ├─ Se SQL: executa query no SQLite → alimenta Step 2
        │       └─ Step 2: LLM gera resposta final (streaming)
        │
        ├─► [Arquivo texto] stream_invoke_with_context() → streaming direto
        │
        └─► [Imagem] stream_invoke_with_image() → streaming via Groq Vision
                │
                ▼
        Salva mensagem no banco + gera título (1ª msg)
                │
                ▼
        Frontend recebe chunks via SSE → renderiza Markdown progressivo
```

---

## Estrutura do Projeto

```
chatbootsite/
├── app.py                          # Ponto de entrada Flask + auto-migração do schema
├── .env                            # Variáveis de ambiente (API key, secret)
├── .gitignore                      # Protege .env, database.db e env/
├── requirements.txt                # Dependências Python
├── database.db                     # Banco de dados SQLite (gerado automaticamente)
│
├── backend/
│   ├── database.py                 # Configuração do SQLAlchemy (SQLite)
│   ├── user.py                     # Modelos ORM: Usuario, Chat, Message
│   ├── routes.py                   # Todas as rotas da API e páginas
│   ├── llm.py                      # Integração Groq: invoke, stream, generate_title
│   ├── db_query.py                 # Schema do banco, execução de queries, correção de SQL
│   ├── file.py                     # Extração de texto: PDF, DOCX, Excel, CSV
│   └── script banco/
│       ├── Create database.sql     # Schema original MySQL (referência)
│       └── banco.sql               # Dados de exemplo (fazendas, vacas, vendas...)
│
├── templates/
│   ├── index.html                  # Interface principal (chat + modal de senha)
│   ├── login.html                  # Tela de login
│   └── cadastro.html               # Tela de cadastro
│
└── static/
    ├── css/
    │   ├── styles.css              # Design system: tema escuro/claro + modal
    │   └── login.css               # Estilos das telas de autenticação
    ├── js/
    │   └── script.js               # Chat streaming (SSE), sidebar, upload, exportar, senha
    └── img/
        └── Logo.png                # Logo UCBvet
```

---

## Banco de Dados

O projeto usa **SQLite** local (`database.db`). As tabelas são criadas e migradas automaticamente na inicialização via `app.py`.

### Tabelas do sistema de chat
| Tabela | Descrição |
|--------|-----------|
| `usuarios` | Usuários com login e senha (hash bcrypt) |
| `chats` | Conversas por usuário, com título e timestamp |
| `messages` | Mensagens de cada conversa (usuário + assistente) |

### Tabelas de dados da empresa
| Tabela | Registros | Descrição |
|--------|-----------|-----------|
| `fazendas` | 16 | Fazendas com endereço |
| `vacas` | 36 | Animais: raça, categoria, ECC, ciclicidade, peso |
| `inseminadores` | 15 | Nomes dos inseminadores |
| `vendedores` | 10 | Vendedores com CPF |
| `vendas` | 25 | Vendas com protocolo, data e valor |
| `visitas` | 24 | Visitas (com e sem venda) |
| `resultados_inseminacao` | 21 | IATF: touro, DG, perda, protocolo |
| `endereco` | 17 | Endereços das fazendas |

---

## Configuração e Instalação

### Pré-requisitos

- Python 3.11+
- Conta Groq com API Key — [console.groq.com](https://console.groq.com)

### 1. Clonar e criar ambiente virtual

```bash
git clone <url-do-repositorio>
cd chatbootsite
python -m venv env
```

**Windows:**
```bash
.\env\Scripts\activate
```

**Linux/Mac:**
```bash
source env/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Edite o arquivo `.env` na raiz do projeto:

```env
GROQ_API_KEY="gsk_sua_chave_aqui"
SECRET_KEY=sua_chave_secreta_flask
```

### 4. Iniciar o servidor

```bash
python app.py
```

Acesse: **http://127.0.0.1:5000**

---

## Uso

### Login e cadastro
Acesse a tela inicial para fazer login. Clique em "Cadastrar" para criar uma nova conta.

### Troca de senha
Na sidebar, clique no ícone de chave (🔑) ao lado do botão de logout. Um modal solicitará a senha atual e a nova senha.

### Chat com banco de dados
O assistente detecta automaticamente quando a pergunta precisa de dados e executa SQL no banco. Exemplos:

```
Quais fazendas temos cadastradas?
Qual a taxa de prenhez geral?
Quais vendedores fizeram mais vendas em 2024?
Quantas vacas são da raça Nelore?
Quais visitas não resultaram em venda?
```

### Memória de conversa
O assistente lembra o contexto da conversa atual. Exemplo:

```
Você:    "Quais fazendas temos?"
UCBvet:  lista as fazendas...
Você:    "E quantas vacas tem a Fazenda Alegria?"  ← referência ao contexto anterior
UCBvet:  responde corretamente
```

### Upload de arquivos
Clique no botão **+** na caixa de mensagem para anexar:
- **Imagens** (JPG, PNG, GIF, WEBP, BMP) — analisadas via Groq Vision
- **Documentos** (PDF, TXT, DOCX, DOC) — texto extraído e enviado ao modelo
- **Planilhas** (XLSX, XLS, CSV) — todas as abas/colunas são lidas

### Exportar conversa
Com uma conversa aberta, clique no botão de download (⬇️) no cabeçalho. O arquivo `.md` baixado contém todo o histórico com data e usuário.

### Parar geração
Clique em **Parar** durante o streaming para cancelar imediatamente a geração da resposta.

---

## Rotas da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Tela de login |
| GET | `/cadastro` | Tela de cadastro |
| GET | `/home` | Interface principal (requer login) |
| GET | `/logout` | Encerrar sessão |
| POST | `/login` | Autenticar usuário |
| POST | `/cadastrar` | Criar novo usuário |
| POST | `/change_password` | Alterar senha do usuário logado |
| GET | `/get_conversations` | Listar conversas do usuário |
| POST | `/add_chat` | Criar nova conversa |
| POST | `/delete_chat/<id>` | Deletar conversa |
| POST | `/update_chat_title/<id>` | Renomear conversa |
| GET | `/get_messages/<id>` | Carregar mensagens de uma conversa |
| POST | `/stream_response/<id>` | Enviar mensagem e receber resposta via SSE (streaming) |
| GET | `/export_chat/<id>` | Baixar conversa em Markdown |

> A rota `/get_response/<id>` (não-streaming) é mantida para compatibilidade.

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11, Flask 3.0 |
| Banco de dados | SQLite via SQLAlchemy 2.0 |
| Autenticação | Flask-Login, Werkzeug (bcrypt) |
| IA / LLM | Groq API — `llama-3.3-70b-versatile` |
| Visão computacional | Groq API — `llama-3.2-11b-vision-preview` |
| Streaming | Server-Sent Events (SSE) — Flask `stream_with_context` |
| Frontend | HTML5, CSS3, JavaScript (vanilla + jQuery) |
| Markdown | marked.js + highlight.js |
| Ícones | Font Awesome 6 |
| Fontes | Syne + Plus Jakarta Sans (Google Fonts) |

---

## Modelos de IA utilizados

| Modelo | Uso |
|--------|-----|
| `llama-3.3-70b-versatile` | Chat, Text-to-SQL, análise de documentos, geração de título |
| `llama-3.2-11b-vision-preview` | Análise de imagens |

---

## Exemplos de perguntas ao banco

```
# Dados operacionais
"Qual a taxa de prenhez nos últimos diagnósticos?"
"Liste as fazendas com mais vacas cadastradas"
"Quais protocolos de sincronização foram mais utilizados?"
"Qual inseminador teve mais IATF realizadas?"
"Qual a média de ECC das vacas por fazenda?"

# Vendas e visitas
"Qual o valor total de vendas por mês?"
"Quais fazendas geraram mais receita?"
"Quantas visitas foram feitas sem resultado em venda?"
"Quais vendedores visitaram mais clientes?"

# Técnico (sem banco)
"O que é ECC e como interpretar os valores?"
"Qual a diferença entre protocolo IATF e CIDR?"
"Como funciona o diagnóstico de gestação por ultrassom?"
"O que significa ciclicidade 0 em uma vaca?"
```

---

## Decisões de arquitetura

### Text-to-SQL em dois passos
O sistema usa dois passos para responder perguntas sobre dados:
1. **Step 1 (rápido, não-streaming)** — LLM analisa a pergunta e o schema; retorna SQL ou resposta direta
2. **Step 2 (streaming)** — LLM interpreta os dados retornados e gera a resposta em linguagem natural

Isso evita alucinações (o modelo não inventa dados) e garante que a resposta sempre reflita o banco real.

### Correção automática de SQL
O módulo `db_query.py` aplica `_fix_sql()` antes de executar qualquer query, corrigindo o padrão mais comum de SQL inválido gerado por LLMs: mistura de `COUNT(*)` com colunas não-agrupadas sem `GROUP BY`.

### Memória limitada
O histórico enviado ao LLM é limitado às últimas **10 mensagens** (`_MAX_HISTORY = 10` em `llm.py`) para evitar estouro de contexto e manter latência baixa.

### Streaming com SSE
A rota `/stream_response` usa `stream_with_context` do Flask para manter o contexto da aplicação durante o streaming. A mensagem é salva no banco **após** o streaming completar. O frontend usa `ReadableStream` (Fetch API) para receber os chunks e renderizar o Markdown progressivamente.
