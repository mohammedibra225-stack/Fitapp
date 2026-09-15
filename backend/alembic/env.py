"""
Configuration Alembic pour Fitapp.

Lit DATABASE_URL depuis backend/.env (meme variable que l'API), pour
ne jamais dupliquer/desynchroniser la config de connexion Neon.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Permet d'importer "app.xxx" quand alembic est lance depuis backend/
sys.path.insert(0, os.getcwd())

load_dotenv()

# Importe tous les modeles pour que Base.metadata les connaisse
# (indispensable pour --autogenerate, voir app/models/__init__.py).
from app.database.base import Base  # noqa: E402
import app.models  # noqa: E402, F401

config = context.config

database_url = os.getenv("DATABASE_URL", "")
if database_url and "sslmode" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}sslmode=require"
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
