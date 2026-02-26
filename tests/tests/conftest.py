import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch

# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def app():
    """Cria aplicação Flask para testes"""
    from app import create_app
    
    app = create_app(testing=True)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Cliente de teste Flask"""
    return app.test_client()

@pytest.fixture
def temp_directory():
    """Diretório temporário para testes"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_db():
    """Mock para banco de dados"""
    with patch('app.extensions.db') as mock:
        mock.session = Mock()
        yield mock

