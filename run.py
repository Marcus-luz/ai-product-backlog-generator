"""
Ponto de entrada da aplicação Flask.

Este arquivo inicia a aplicação com a configuração apropriada
baseada na variável de ambiente FLASK_CONFIG.
"""

import os
from dotenv import load_dotenv
from app import create_app

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)