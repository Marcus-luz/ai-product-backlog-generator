import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from sqlalchemy.exc import IntegrityError # Importa o erro que esperamos do DB
from app.models.product import Product
from app.models.persona import Persona # Importa o modelo Persona
from app.models.revision import Revision # Importa o modelo Revision
import json
from app.models.epic import Epic
from app.models.user_story import UserStory


@pytest.fixture
def test_app():
    """
    Cria uma instância do app Flask para testes com um banco de dados em memória.
    """
    # Usa a configuração de teste que definimos anteriormente em config.py
    # Se não tiver, adicione:
    # class TestingConfig(Config):
    #     TESTING = True
    #     SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    app = create_app('testing')
    with app.app_context():
        # Cria todas as tabelas para o banco de dados em memória
        db.create_all()
        yield app  # Fornece o app para os testes
        # Limpa o banco de dados no final
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def sample_user(test_app):
    """
    Cria e salva um usuário de exemplo no banco de dados para ser usado nos testes.
    O 'scope=function' garante que um novo usuário seja criado para cada função de teste.
    """
    user = User(username='test_owner', email='owner@test.com')
    user.set_password('123')
    db.session.add(user)
    db.session.commit()
    return user


class TestUserModel:
    """Testes para o modelo User."""

    def test_password_hashing(self, test_app):
        """
        Testa se a senha é corretamente hasheada e verificada.
        """
        # Arrange
        user = User(username='testuser', email='test@example.com')
        
        # Act
        user.set_password('mysecretpassword')
        
        # Assert
        assert user.password_hash is not None
        assert user.password_hash != 'mysecretpassword' # Garante que a senha não foi salva em texto plano
        assert user.check_password('mysecretpassword') is True
        assert user.check_password('wrongpassword') is False

    def test_unique_username(self, test_app):
        """
        Testa se o banco de dados impõe a restrição de username único.
        """
        # Arrange: Cria e salva um primeiro usuário
        user1 = User(username='unique_user', email='user1@example.com')
        user1.set_password('123')
        db.session.add(user1)
        db.session.commit()

        # Cria um segundo usuário com o mesmo username
        user2 = User(username='unique_user', email='user2@example.com')
        user2.set_password('456')
        db.session.add(user2)
        
        # Act & Assert: Espera-se um IntegrityError ao tentar salvar o segundo usuário
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        # Desfaz a transação falha para não afetar outros testes
        db.session.rollback()

    def test_unique_email(self, test_app):
        """
        Testa se o banco de dados impõe a restrição de e-mail único.
        """
        # Arrange: Cria e salva um primeiro usuário
        user1 = User(username='user_a', email='unique@example.com')
        user1.set_password('123')
        db.session.add(user1)
        db.session.commit()

        # Cria um segundo usuário com o mesmo e-mail
        user2 = User(username='user_b', email='unique@example.com')
        user2.set_password('456')
        db.session.add(user2)
        
        # Act & Assert: Espera-se um IntegrityError
        with pytest.raises(IntegrityError):
            db.session.commit()
            
        db.session.rollback()

    def test_repr_method(self, test_app):
        """
        Testa a representação em string do objeto User.
        """
        user = User(username='repr_test', email='repr@test.com')
        assert repr(user) == '<User repr_test>'
        
class TestProductModel:
    """Testes para o modelo Product."""

    def test_product_creation(self, test_app, sample_user):
        """
        Testa a criação bem-sucedida de um produto com um dono.
        """
        # Arrange & Act
        product = Product(
            name="Meu Produto de Teste",
            description="Uma descrição detalhada.",
            value_proposition="Resolver um problema X.",
            owner_id=sample_user.id  # Associa o produto ao usuário criado pela fixture
        )
        db.session.add(product)
        db.session.commit()
        
        # Assert
        # Busca o produto no banco para verificar se foi salvo corretamente
        saved_product = Product.query.get(product.id)
        assert saved_product is not None
        assert saved_product.name == "Meu Produto de Teste"
        assert saved_product.owner_id == sample_user.id
        assert saved_product.owner.username == 'test_owner' # Verifica o relacionamento de volta ao usuário
        assert saved_product.created_at is not None # Verifica se a data de criação foi definida

    def test_product_requires_name(self, test_app, sample_user):
        """
        Testa que um produto não pode ser criado sem um nome (nullable=False).
        """
        # Arrange: Cria um produto sem o campo 'name'
        product = Product(description="Produto sem nome", owner_id=sample_user.id)
        db.session.add(product)
        
        # Act & Assert: Espera-se um IntegrityError ao tentar salvar
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback() # Limpa a transação falha

    def test_product_requires_owner(self, test_app):
        """
        Testa que um produto não pode ser criado sem um dono (owner_id nullable=False).
        """
        # Arrange: Cria um produto sem associá-lo a um usuário
        product = Product(name="Produto Órfão", description="...")
        db.session.add(product)
        
        # Act & Assert: Espera-se um IntegrityError
        with pytest.raises(IntegrityError):
            db.session.commit()
            
        db.session.rollback()
        
    def test_product_persona_relationship(self, test_app, sample_user):
        """
        Testa o relacionamento entre Produto e Persona.
        """
        # Arrange: Cria um produto e uma persona associada a ele
        product = Product(name="Produto com Persona", owner=sample_user)
        persona = Persona(name="Comprador Ideal", product=product) # Associa usando o backref
        
        db.session.add(product)
        db.session.add(persona)
        db.session.commit()
        
        # Assert
        # Verifica se a persona está na lista de personas do produto
        assert product.personas.count() == 1
        assert product.personas.first().name == "Comprador Ideal"
        # Verifica se o produto está corretamente associado a partir da persona
        assert persona.product.name == "Produto com Persona"
    
# Em tests/test_models.py

class TestRevisionModel:
    """Testes para o modelo Revision."""

    def test_revision_creation(self, test_app, sample_user):
        """
        Testa a criação bem-sucedida de um registro de revisão.
        """
        # Arrange
        revision_content = {'data': 'novo conteúdo do artefato'}
        
        # Act
        revision = Revision(
            artifact_id=1,
            artifact_type='epic',
            content=json.dumps(revision_content),
            change_description="Criação inicial do épico",
            reviser=sample_user # Associa diretamente ao objeto User
        )
        db.session.add(revision)
        db.session.commit()
        
        # Assert
        saved_revision = Revision.query.get(revision.id)
        assert saved_revision is not None
        assert saved_revision.artifact_type == 'epic'
        assert saved_revision.user_id == sample_user.id
        assert saved_revision.reviser.username == 'test_owner'
        assert saved_revision.timestamp is not None
        assert json.loads(saved_revision.content)['data'] == 'novo conteúdo do artefato'

    def test_revision_creation_sem_usuario(self, test_app):
        """
        Testa a criação de uma revisão sem um usuário associado (ex: mudança automática).
        """
        # Arrange & Act
        # O campo user_id é nullable=True, então esta operação deve ser válida.
        revision = Revision(
            artifact_id=2,
            artifact_type='user_story',
            content='{"status": "auto-updated"}'
        )
        db.session.add(revision)
        db.session.commit()
        
        # Assert
        saved_revision = Revision.query.get(revision.id)
        assert saved_revision is not None
        assert saved_revision.user_id is None
        assert saved_revision.reviser is None

