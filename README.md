# 🚀 Assistente de Geração de Artefatos Ágeis

> Sistema de apoio à geração de artefatos para metodologias ágeis usando Large Language Models (LLMs)

**Acesse o projeto online:** [Assistente de Geração de Artefatos Ágeis](https://agile-artifacts-assistant.onrender.com)

## 📋 Sobre o Projeto
Este sistema utiliza modelos de linguagem avançados para auxiliar equipes ágeis na criação e gerenciamento de diversos artefatos como épicos, histórias de usuário, requisitos e product backlog. Ideal para times que desejam acelerar seus processos de documentação mantendo consistência e qualidade.

Desenvolvido com Flask e PostgreSQL, o sistema oferece uma interface web intuitiva para gerenciar produtos, épicos, user stories e backlog de forma automatizada.

## 🛠️ Instalação

### Pré-requisitos
- Python 3.12.10 estável
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
## 🛠 Solução de Problemas (Troubleshooting)
1. Erro: No module named poetry ou Falha no poetry install
Causa: O Poetry não está disponível ou não está vinculado à versão do Python em uso (ex: Python 3.14).

Solução: Force a instalação do Poetry via PIP e use o módulo do Python para instalar as dependências:
```bash
pip install poetry
python -m poetry install
```
### Banco de Dados
O sistema utiliza PostgreSQL com SQLAlchemy ORM e Alembic para migrações. Para configurar:

1. Instale o PostgreSQL
2. Crie o banco de dados `product_owner_db`
3. Configure a variável `DATABASE_URL` no arquivo `.env`
4. Execute as migrações: `poetry run alembic upgrade head`

## 🗂️ Estrutura do Projeto

```
problema-4/
├── .pytest_cache/                  # Metadados e cache de execução do Pytest
│   ├── CACHEDIR.TAG
│   ├── README.md
│   └── v/
│       └─ cache/
│           ├── lastfailed          # Armazena os últimos testes que falharam para re-execução rápida
│           └── nodeids             # IDs de referência para os nós de teste
├── alembic.ini                     # Configuração do Alembic para controle de migrações de banco de dados
├── app/                            # Núcleo da aplicação desenvolvida em Python/Flask
│   ├── extensions.py               # Inicialização de extensões (SQLAlchemy, JWT, etc.)
│   ├── models/                     # Camada de Modelos de Dados (SQLAlchemy ORM)
│   │   ├── backlog.py              # Definição da estrutura do Backlog do Produto
│   │   ├── epic.py                 # Modelo para agrupamento de requisitos (Épicos)
│   │   ├── persona.py              # Definição de perfis de usuários do sistema
│   │   ├── product.py              # Modelo central para gestão de produtos
│   │   ├── requirement.py          # Estrutura para requisitos funcionais/não-funcionais
│   │   ├── revision.py             # Log de histórico e versões de alterações
│   │   ├── user.py                 # Modelo de Usuário e credenciais
│   │   ├── user_story.py           # Estrutura para Histórias de Usuário
│   │   └── __init__.py
│   ├── routes/                     # Organização de rotas via Blueprints
│   │   ├── auth.py                 # Fluxos de autenticação, login e registro
│   │   ├── backlog_bp.py           # Gestão e visualização do backlog
│   │   ├── dashboard_bp.py         # Painel principal de métricas do sistema
│   │   ├── epic_bp.py              # Endpoints para manipulação de Épicos
│   │   ├── product_bp.py           # CRUD e gestão de produtos
│   │   ├── requirement_bp.py       # Gestão do ciclo de vida de requisitos
│   │   ├── settings_bp.py          # Configurações de conta e sistema
│   │   └── user_story_bp.py        # Endpoints para User Stories
│   ├── services/                   # Camada de Serviços (Lógica de Negócio isolada)
│   │   ├── backlog_service.py      # Processamento de priorização do backlog
│   │   ├── epic_service.py         # Lógica para criação e refinamento de Épicos
│   │   ├── llm_service.py          # Integração com Groq e modelos de IA
│   │   ├── logging_service.py      # Auditoria de interações e métricas de sistema
│   │   ├── product_service.py      # Lógica de negócio vinculada a produtos
│   │   ├── requirement_service.py  # Regras para validação de requisitos
│   │   └── user_story_service.py   # Gerenciamento de histórias de usuário
│   ├── static/                     # Ativos estáticos servidos pelo Flask
│   │   ├── css/
│   │   │   └── style.css           # Estilização principal do sistema
│   │   ├── favicon.ico             # Ícone do navegador
│   │   ├── img/                    # Ativos visuais (Logos, imagens de fundo)
│   │   │   ├── login_image.png
│   │   │   └── system_logo.png
│   │   └── js/
│   │       └── main.js             # Scripts para interatividade no frontend
│   ├── templates/                  # Templates HTML utilizando o motor Jinja2
│   │   ├── auth/
│   │   │   ├── login.html          # Interface de acesso ao sistema
│   │   │   └── register.html       # Interface de criação de conta
│   │   ├── backlog.html            # Visualização do Backlog do Produto
│   │   ├── base.html               # Layout mestre herdado pelas demais páginas
│   │   ├── dashboard.html          # Página principal com métricas
│   │   ├── epics.html              # Listagem e gestão de Épicos
│   │   ├── products.html           # Gestão de portfólio de produtos
│   │   ├── product_detail.html     # Visão detalhada de um produto específico
│   │   ├── requirements.html       # Central de requisitos
│   │   └── stories.html            # Visualização de User Stories
│   ├── utils/                      # Scripts auxiliares e helpers
│   │   └── prompt_templates.py     # Estruturas de prompts para otimização da IA
│   └── __init__.py                 # Padrão Application Factory para inicialização
├── config.py                       # Configurações de ambiente (Desenvolvimento, Teste, Produção)
├── cypress/                        # Framework para testes de ponta a ponta (E2E) e BDD
│   ├── e2e/                        # Cenários de teste e especificações
│   │   ├── dashboard.cy.js         # Validação de interface do Dashboard
│   │   ├── login.cy.js             # Validação funcional do fluxo de login
│   │   ├── produto.feature         # Cenários documentados em Gherkin
│   │   └── step_definitions/
│   │       └── produto_steps.js    # Implementação técnica dos passos Gherkin
│   ├── fixtures/                   # Dados mockados para simulação de respostas
│   │   └── example.json
│   └── support/                    # Configurações e comandos globais do Cypress
│       ├── commands.js             # Customização de comandos (ex: cy.login())
│       └── e2e.js                  # Configuração global de ambiente de teste
├── cypress.config.js               # Arquivo central de configuração do Cypress
├── locustfile.py                   # Script para testes de carga e performance com Locust
├── logs/                           # Armazenamento de logs de auditoria
│   ├── llm_interactions_2025-07.jsonl # Histórico de interações com IA de Julho/2025
│   └── llm_interactions_2026-02.jsonl # Histórico de interações recente (Fevereiro/2026)
├── migrations/                     # Scripts de evolução do esquema do Banco de Dados
│   ├── env.py                      # Ambiente de execução do Alembic
│   ├── README                      # Documentação das migrações
│   ├── script.py.mako              # Template para novos scripts de migração
│   └── versions/                   # Histórico cronológico das alterações no DB
│       ├── 3353bf69da4a_increase_password_hash_length.py
│       ├── 789a8f8ff6f4_initial_database_setup.py
│       ├── add_generated_by_llm_epics.py
│       ├── add_llm_interactions_table.py
│       └── e9bf6b2f031b_add_generated_by_llm_to_requirements.py
├── package-lock.json               # Versões travadas de dependências Node.js
├── package.json                    # Scripts e dependências para Cypress e ferramentas JS
├── poetry.lock                     # Versões travadas das dependências Python
├── pyproject.toml                  # Manifesto de projeto e dependências via Poetry
├── README.md                       # Documentação técnica principal do repositório
├── render.yaml                     # Configuração para Deployment na plataforma Render
├── run.py                          # Script de entrada para execução local do servidor
├── runtime.txt                     # Especificação da versão do Python para ambientes de nuvem
└── tests/                          # Suíte de testes automatizados do Backend (Pytest)
    └─ tests/
        ├── conftest.py             # Configurações e Fixtures compartilhadas do Pytest
        ├── test_auth.py            # Testes unitários para serviços de autenticação
        ├── test_llm_service.py     # Testes de integração com a API de LLM
        ├── test_logging_service.py # Testes do sistema de auditoria e logs
        ├── test_models.py          # Validação das restrições e esquemas dos modelos ORM
        └── __init__.py
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

## 🧪 Qualidade de Software (QA)

O projeto possui uma suíte robusta de testes automatizados, cobrindo múltiplas camadas da aplicação para garantir a estabilidade das funcionalidades, da interface e da integração com a Inteligência Artificial.

### 🛠️ 1. Testes de Back-end (Caixa Branca e Unitários)
Utilizamos o **Pytest** para validar as regras de negócio internas, serviços de autenticação, operações de base de dados e a comunicação com a API do Groq. A suíte abrange:
* **Autenticação**: Validação de login e registo.
* **Modelos**: Integridade das entidades do banco de dados.
* **Serviços de IA**: Construção e resposta de prompts.
* **Logging**: Rastreabilidade de interações.

* **Como executar:**
  ```bash
  poetry run pytest

### 🖥️ 2. Testes Ponta a Ponta / E2E (Caixa Preta)
Utilizamos o Cypress para simular a navegação de um usuário real, garantindo o funcionamento do fluxo de login e a criação de produtos. É importante ressaltar que o servidor Flask deve estar em execução através do comando **poetry run python run.py** para que o Cypress interaja com a aplicação. Para realizar os testes, você pode abrir a interface visual e interativa com **npx cypress open** ou optar pela execução direta em modo terminal (headless) utilizando **npx cypress run**.

### 📖 3. BDD (Behavior-Driven Development)
Integramos o Cucumber ao Cypress para documentar e testar requisitos em linguagem natural via Gherkin, permitindo que os critérios de aceitação sejam validados automaticamente. O arquivo de cenários está localizado em **cypress/e2e/produto. feature** e, para validar os cenários de negócio em tempo real, basta selecionar este arquivo **.feature** ao abrir a interface do Cypress.

### 🚀 4. Testes de Performance e Carga (Não-Funcionais)
Utilizamos o Locust para avaliar a resiliência do sistema e o comportamento do backend sob estresse, simulando múltiplos usuários simultâneos. Em nossos benchmarks (v1.0), com uma carga simulada de 50 usuários simultâneos (Spawn rate: 5/s), o sistema atingiu um throughput de aproximadamente 25.2 RPS e um tempo de resposta médio de 12ms para renderização de views e acesso ao Dashboard, bloqueando acessos não autenticados em apenas 3ms. Para executar a simulação, inicie o servidor com **poetry run locust** e acesse **http://localhost:8089** para configurar o **host http://127.0.0.1:5000.**


# 📚 Visualização do Sistema
- **Login**
<img width="1158" height="571" alt="AI-Product-Owner" src="https://github.com/user-attachments/assets/101b8af0-12cd-4475-afba-2681c0a7fc8f" />


- **Produto**
<img width="1913" height="912" alt="ia produt" src="https://github.com/user-attachments/assets/3ffb59e3-0a13-4f14-9825-1f24a6d8ab6c" />


- **Épicos**
<img width="1892" height="902" alt="ia2" src="https://github.com/user-attachments/assets/08da4e4a-ec62-4eca-9165-b084bf04bd96" />


- **História**
<img width="1878" height="918" alt="ia3" src="https://github.com/user-attachments/assets/3d53eef5-1e97-4bf1-a53e-9fbaf552bbe3" />


- **Requisitos**
<img width="1867" height="913" alt="ia4" src="https://github.com/user-attachments/assets/39e38af4-2158-406d-8a22-55b401101fca" />


