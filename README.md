# 🚀 Assistente de Geração de Artefatos Ágeis

> Sistema de apoio à geração de artefatos para metodologias ágeis usando Large Language Models (LLMs)

## 📋 Sobre o Projeto
Este sistema utiliza modelos de linguagem avançados para auxiliar equipes ágeis na criação e gerenciamento de diversos artefatos como épicos, histórias de usuário, requisitos e product backlog. Ideal para times que desejam acelerar seus processos de documentação mantendo consistência e qualidade.

Desenvolvido com Flask e PostgreSQL, o sistema oferece uma interface web intuitiva para gerenciar produtos, épicos, user stories e backlog de forma automatizada.

## 🛠️ Instalação

### Pré-requisitos
- Python 3.11+
- Poetry (gerenciador de dependências)
- PostgreSQL 12+
- Acesso a uma API de LLM (Groq)

### Passo a passo
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/grupo-06.git
cd grupo-06/problema-4

# Instale o Poetry (se não tiver instalado)
# Windows PowerShell:
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Instale as dependências do projeto
poetry install

# Configure o banco de dados PostgreSQL
# Certifique-se de que o PostgreSQL está rodando
# Crie o banco de dados: product_owner_db

# Configure as variáveis de ambiente
# Crie um arquivo .env na raiz do projeto com:
# SECRET_KEY=sua_chave_secreta_muito_segura
# DATABASE_URL=postgresql://postgres:sua_senha@localhost:5432/product_owner_db
# GROQ_API_KEY=sua_chave_da_api_groq
# FLASK_CONFIG=development

# Execute as migrações do banco de dados
poetry run alembic upgrade head

# Execute a aplicação
poetry run python run.py
```

## 🔧 Configuração
Configure as variáveis de ambiente no arquivo `.env` conforme necessário:

```env
# Configurações essenciais
SECRET_KEY=sua_chave_secreta_muito_segura
DATABASE_URL=postgresql://postgres:sua_senha@localhost:5432/product_owner_db
GROQ_API_KEY=sua_chave_da_api_groq
FLASK_CONFIG=development

# Configurações JWT (opcionais)
JWT_SECRET_KEY=sua_chave_jwt
```

### Banco de Dados
O sistema utiliza PostgreSQL com SQLAlchemy ORM e Alembic para migrações. Para configurar:

1. Instale o PostgreSQL
2. Crie o banco de dados `product_owner_db`
3. Configure a variável `DATABASE_URL` no arquivo `.env`
4. Execute as migrações: `poetry run alembic upgrade head`

## 🗂️ Estrutura do Projeto

```
PROBLEMA-4/
├── pyproject.toml            # Configuração do Poetry e dependências
├── alembic.ini              # Configuração do Alembic (migrações)
├── config.py                # Configurações da aplicação (desenvolvimento, produção, teste)
├── run.py                   # Ponto de entrada da aplicação (executa o Flask app)
├── README.md                # Descrição do projeto e instruções
├── venv/                    # Ambiente virtual Python (criado pelo Poetry)
├── logs/                    # Arquivos de log da aplicação
├── migrations/              # Migrações do banco de dados (Alembic)
├── tests/                   # Testes automatizados
│   ├── conftest.py          # Configuração dos testes
│   ├── test_auth.py         # Testes de autenticação
│   ├── test_llm_service.py  # Testes do serviço LLM
│   ├── test_logging_service.py # Testes do serviço de logging
│   └── test_models.py       # Testes dos modelos
├── app/                     # Lógica principal da aplicação
│   ├── __init__.py          # Inicializa o Flask app e registra Blueprints
│   ├── extensions.py        # Inicializa extensões Flask (SQLAlchemy, JWT, etc.)
│   ├── models/              # Modelos de dados (SQLAlchemy ORM)
│   │   ├── __init__.py
│   │   ├── user.py          # Modelo para Usuários (autenticação)
│   │   ├── product.py       # Modelo para Produtos
│   │   ├── epic.py          # Modelo para Épicos
│   │   ├── user_story.py    # Modelo para Histórias de Usuário
│   │   ├── requirement.py   # Modelo para Requisitos
│   │   ├── backlog.py       # Modelo para Product Backlog
│   │   ├── persona.py       # Modelo para Personas
│   │   ├── revision.py      # Modelo para Histórico de Revisões
│   │   └── llm_interaction.py # Modelo para Interações com LLM
│   ├── routes/              # Blueprints (rotas e lógica de negócio)
│   │   ├── auth.py          # Rotas de autenticação (login, registro)
│   │   ├── product_bp.py    # Rotas para gestão de produtos
│   │   ├── dashboard_bp.py  # Rotas do dashboard principal
│   │   ├── epic_bp.py       # Rotas para Épicos (geração, edição)
│   │   ├── user_story_bp.py # Rotas para Histórias de Usuário
│   │   ├── requirement_bp.py # Rotas para Requisitos
│   │   ├── backlog_bp.py    # Rotas para o Product Backlog
│   │   └── settings_bp.py   # Rotas de configurações
│   ├── services/            # Serviços de negócio e lógica complexa
│   │   ├── __init__.py
│   │   ├── llm_service.py   # Integração com APIs de LLMs (Groq)
│   │   ├── logging_service.py # Registro detalhado de logs e métricas
│   │   ├── product_service.py # Lógica de negócio para produtos
│   │   ├── epic_service.py  # Lógica de negócio para épicos
│   │   ├── user_story_service.py # Lógica de negócio para user stories
│   │   ├── requirement_service.py # Lógica de negócio para requisitos
│   │   └── backlog_service.py # Lógica de negócio para backlog
│   ├── utils/               # Funções utilitárias e helpers
│   │   ├── __init__.py
│   │   ├── decorators.py    # Decoradores para validação, autenticação
│   │   └── prompt_templates.py # Templates de prompts para LLMs
│   ├── templates/           # Arquivos HTML para o frontend Flask
│   │   ├── base.html        # Template base
│   │   ├── dashboard.html   # Dashboard principal
│   │   ├── products.html    # Lista de produtos
│   │   ├── product_detail.html # Detalhes do produto
│   │   ├── epics.html       # Gestão de épicos
│   │   ├── stories.html     # Gestão de user stories
│   │   ├── requirements.html # Gestão de requisitos
│   │   ├── backlog.html     # Product backlog
│   │   └── auth/            # Templates de autenticação
│   └── static/              # Arquivos estáticos (CSS, JS, imagens)
│       ├── css/
│       ├── js/
│       └── img/
└── __pycache__/             # Cache do Python
```

## 📚 Funcionalidades Principais

### 🏢 Gestão de Produtos
- **Cadastro de Produtos**: Criação e gerenciamento de produtos de software
- **Dashboard Centralizado**: Visão geral de todos os produtos e seus artefatos
- **Detalhamento**: Visualização completa de informações do produto

### 📖 Épicos
- **Geração Automatizada**: Criação de épicos usando IA baseada em descrições de produto
- **Edição e Refinamento**: Interface para editar e refinar épicos gerados
- **Rastreabilidade**: Conexão entre épicos e outros artefatos

### 👥 Histórias de Usuário  
- **Geração Inteligente**: Criação automática de user stories a partir de épicos
- **Personas**: Sistema de personas para contextualizar as histórias
- **Critérios de Aceite**: Geração automática de critérios de aceite

### 📋 Requisitos
- **Extração Automática**: Identificação de requisitos funcionais e não-funcionais
- **Priorização**: Sistema de priorização baseado em critérios definidos
- **Rastreabilidade**: Conexão entre requisitos e suas origens

### 🎯 Product Backlog
- **Organização Automática**: Estruturação inteligente do backlog
- **Priorização Sugerida**: Algoritmos para sugestão de prioridades
- **Métricas**: Acompanhamento de métricas do backlog

### 🔧 Funcionalidades Técnicas
- **Autenticação JWT**: Sistema seguro de autenticação
- **Logging Avançado**: Rastreamento detalhado de operações e interações com IA
- **API REST**: Endpoints para integração com outras ferramentas
- **Migrações**: Sistema robusto de versionamento do banco de dados

## 🔄 Fluxo de Trabalho

1. **Login**: Acesse o sistema através da autenticação JWT
2. **Dashboard**: Visualize todos os produtos e seus status no painel principal
3. **Cadastro de Produto**: Registre um novo produto com suas características principais
4. **Geração de Épicos**: Use IA para gerar épicos automaticamente ou crie manualmente
5. **Histórias de Usuário**: Para cada épico, gere user stories detalhadas com personas
6. **Requisitos**: Extraia e organize requisitos específicos a partir das histórias
7. **Backlog**: Organize e priorize automaticamente o product backlog
8. **Monitoramento**: Acompanhe métricas e logs de todas as operações

## 🧪 Testes

Execute os testes automatizados com Poetry:

```bash
# Executar todos os testes
poetry run pytest

# Executar testes com coverage
poetry run pytest --cov=app

# Executar testes específicos
poetry run pytest tests/test_auth.py
poetry run pytest tests/test_llm_service.py
```

## 🚀 Tecnologias Utilizadas

- **Backend**: Flask 3.1.1
- **Banco de Dados**: PostgreSQL com SQLAlchemy ORM
- **Migrações**: Alembic
- **Autenticação**: Flask-Login + JWT Extended
- **IA/LLM**: Groq API
- **Gerenciamento de Dependências**: Poetry
- **Testes**: pytest
- **Frontend**: HTML5, CSS3, JavaScript (templates Jinja2)

## 👥 Equipe

- **Alessandro Oliveira** - [alessandrooliveira.aluno@unipampa.edu.br](mailto:alessandrooliveira.aluno@unipampa.edu.br)
- **Leonardo Paulino de Oliveira** - [leonardopaulino.aluno@unipampa.edu.br](mailto:leonardopaulino.aluno@unipampa.edu.br)
- **Guilherme Oviedo Nunes** - [guilhermeoviedo.aluno@unipampa.edu.br](mailto:guilhermeoviedo.aluno@unipampa.edu.br)
- **Marcus Vinicius da Luz Araujo** - [marcusaraujo.aluno@unipampa.edu.br](mailto:marcusaraujo.aluno@unipampa.edu.br)

## 📝 Notas de Desenvolvimento

### Comandos Úteis

```bash
# Ativar ambiente Poetry
poetry shell

# Adicionar nova dependência
poetry add nome-do-pacote

# Criar nova migração
poetry run alembic revision --autogenerate -m "Descrição da migração"

# Aplicar migrações
poetry run alembic upgrade head

# Reverter migração
poetry run alembic downgrade -1

# Executar aplicação em modo desenvolvimento
poetry run python run.py
```

### Estrutura de Logs
Os logs são organizados em categorias:
- **Aplicação**: Logs gerais do Flask
- **LLM**: Interações com modelos de linguagem
- **Performance**: Métricas de desempenho
- **Autenticação**: Eventos de login/logout

