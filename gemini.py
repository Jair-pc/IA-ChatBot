import google.generativeai as genai
import os
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Gemini
genai.configure(api_key=os.getenv('API_KEY'))

# Função para iniciar o chat
def start_chat():
    model = genai.GenerativeModel('gemini-pro')
    return model.start_chat(history=[])

# Função para obter resposta do Gemini
def get_gemini_response(user_message):
    try:
        if 'chat' not in globals():
            global chat
            chat = start_chat()
        
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        logger.error(f"Error generating response: {e}, User message: {user_message}")
        return "Erro ao obter resposta do servidor."
