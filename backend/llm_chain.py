from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Carregar modelo de linguagem Google Gemini
def load_llm_model():
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        api_key=os.getenv('GOOGLE_API_KEY'),
        temperature=0.7,
        default_language="pt"
    )
    return llm

# Criar o prompt template para o modelo
def create_prompt_template():
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
        Você é um chatbot capaz de responder a perguntas relacionadas ao banco de dados e fornecer informações gerais como o ChatGPT.
        Todas as suas respostas devem ser em português.
        Contexto: {context}
        Pergunta: {question}
        Resposta (em português):
        """
    )
    return prompt_template

# Função para gerar resposta usando o modelo de linguagem
def generate_response(question, context=""):
    # Carregar o modelo
    llm = load_llm_model()

    # Criar o prompt template
    prompt_template = create_prompt_template()

    # Configurar a Chain
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Gerar resposta
    response = chain.run(context=context, question=question)
    return response
