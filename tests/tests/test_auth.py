
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User # Import User para o teste de login
import json

@pytest.fixture(scope='module')
def test_client():
    """
    Cria um cliente de teste do Flask para os testes de autenticação.
    Usa uma configuração de teste com um banco de dados SQLite em memória.
    """
    flask_app = create_app('testing') 

    with flask_app.app_context():
        db.create_all()
        yield flask_app.test_client()
        db.session.remove()
        db.drop_all()

def test_register_success(test_client):
    """
    Testa o registro de um novo usuário com sucesso.
    """
    response = test_client.post('/auth/register',
                                json={
                                    "username": "testuser",
                                    "email": "test@example.com",
                                    "password": "password123"
                                })
    data = json.loads(response.data)
    
    assert response.status_code == 201
    # CORREÇÃO: Verifica a mensagem em português
    assert "User registrado com sucesso" in data['message']

def test_register_existing_user(test_client):
    """
    Testa a tentativa de registrar um usuário que já existe.
    """
    # Não precisamos criar o usuário duas vezes, o test_client é reutilizado, mas o DB não é limpo entre funções
    # Uma melhor prática seria usar fixtures com 'scope=function' se os testes precisarem de um DB limpo sempre.
    # Por agora, vamos assumir que 'testuser' já foi criado no teste anterior.
    response = test_client.post('/auth/register', json={"username": "testuser", "email": "another@example.com", "password": "password123"})
    data = json.loads(response.data)
    
    assert response.status_code == 409
    # CORREÇÃO: Verifica a mensagem em português
    assert "Username ja existe" in data['message']

def test_login_success(test_client):
    """
    Testa o login com credenciais corretas.
    """
    # Arrange: Garante que o usuário para login exista.
    # Em vez de depender do teste anterior, vamos criá-lo aqui para que o teste seja independente.
    user = User(username='loginuser', email='login@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # Act: Tenta fazer login
    response = test_client.post('/auth/login', json={"username": "loginuser", "password": "password123"})
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert "access_token" in data

def test_login_invalid_credentials(test_client):
    """
    Testa o login com senha incorreta.
    """
    response = test_client.post('/auth/login', json={"username": "loginuser", "password": "wrongpassword"})
    data = json.loads(response.data)
    
    assert response.status_code == 401
    # CORREÇÃO: Verifica a mensagem em português
    assert "Credenciais inválidas" in data['message']
    
def test_register_missing_fields(test_client):
    """
    Testa o registro com campos faltando e espera um erro 400.
    """
    response = test_client.post('/auth/register', json={"username": "testuser_missing"})
    data = json.loads(response.data)

    assert response.status_code == 400
    # CORREÇÃO: Verifica a mensagem em português
    assert "Username, email e senha são requeridos" in data['message']

def test_login_missing_fields(test_client):
    """
    Testa o login com o campo de senha faltando e espera um erro 400.
    """
    response = test_client.post('/auth/login', json={"username": "testuser"})
    data = json.loads(response.data)

    assert response.status_code == 400
    # CORREÇÃO: Verifica a mensagem em português
    assert "Username e senha requeridos" in data['message']
    
def test_register_existing_email(test_client):
    """
    Testa a tentativa de registrar com um e-mail que já existe.
    """
    # O e-mail 'test@example.com' foi usado em test_register_success
    response = test_client.post('/auth/register', json={"username": "user2", "email": "test@example.com", "password": "456"})
    
    assert response.status_code == 409
    data = json.loads(response.data)
    # CORREÇÃO: Verifica a mensagem em português
    assert "Email ja existe" in data['message']
    
# Os outros testes (rotas protegidas, renderização de páginas) não dependem de mensagens JSON,
# então eles provavelmente já estavam passando ou não precisam de correção de idioma.
# Mantendo-os aqui para completude.

def test_protected_route_with_valid_token(test_client):
    """
    Testa o acesso a uma rota protegida com um token JWT válido.
    """
    login_response = test_client.post('/auth/login', json={"username": "loginuser", "password": "password123"})
    token = json.loads(login_response.data)['access_token']
    
    headers = {'Authorization': f'Bearer {token}'}
    protected_response = test_client.get('/auth/protected', headers=headers)
    
    assert protected_response.status_code == 200
    data = json.loads(protected_response.data)
    # CORREÇÃO: Verifica a mensagem em português
    assert "Olá, loginuser! Você está autenticado." in data['message']

def test_protected_route_no_token(test_client):
    """
    Testa o acesso a uma rota protegida sem um token e espera um erro 401.
    """
    response = test_client.get('/auth/protected')
    assert response.status_code == 401
    
@pytest.mark.parametrize("page_url", [
    "/auth/login_page",
    "/auth/register_page"
])
def test_render_pages_successfully(test_client, page_url):
    """
    Testa se as páginas de login e registro são carregadas com sucesso (status 200).
    """
    response = test_client.get(page_url)
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'

def test_logout_redirects(test_client):
    """
    Testa se a rota de logout redireciona para a página de login.
    """
    response = test_client.get('/auth/logout')
    
    assert response.status_code == 302
    assert response.location == '/auth/login_page'