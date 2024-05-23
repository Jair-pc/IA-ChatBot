from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicialização do MySQL
mysql = MySQL()

def configure_db(app):
    # Configuração do MySQL
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
    mysql.init_app(app)

def executar_consulta(query, params=None):
    try:
        with mysql.connection.cursor() as cursor:
            cursor.execute(query, params)
            resultado = cursor.fetchall()
        return resultado
    except Exception as e:
        return str(e)
