# migrations/env.py

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- INÍCIO DAS IMPORTAÇÕES E CONFIGURAÇÕES DO FLASK ---
from flask import current_app
from app import create_app
from config import config_by_name

# Este é o objeto de configuração Alembic, obtido do alembic.ini
config = context.config

# Crie e configure o aplicativo Flask para que o Alembic possa acessar suas configurações e modelos.
# Isso é essencial para que db.metadata seja carregado corretamente.
config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)
app.app_context().push() # Empurra o contexto do aplicativo

# O Alembic precisa de uma URL de banco de dados. Vamos obtê-la do Flask app.config.
config.set_main_option('sqlalchemy.url', current_app.config.get('SQLALCHEMY_DATABASE_URI'))

# Importa a instância 'db' do SQLAlchemy que contém todos os seus modelos
from app.extensions import db
target_metadata = db.metadata # Isso informa ao Alembic onde encontrar os metadados dos seus modelos
# --- FIM DAS IMPORTAÇÕES E CONFIGURAÇÕES DO FLASK ---

# Interpretar o arquivo de configuração para logging
fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is additionally needed
    for Alembic to entirely work properly.
    By skipping the Engine creation we don't even need a DBAPI to be
    available. Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True # Adicionado para operações de ALTER TABLE que podem ser mais robustas
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()