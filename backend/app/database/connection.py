

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL manquante. Definissez-la dans backend/.env "
        "(voir .env.example) avec votre chaine de connexion Neon."
    )

# Neon exige TLS. On force sslmode=require si l'utilisateur ne l'a pas
# deja precise dans sa chaine de connexion.
if "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

# pool_pre_ping evite les erreurs de connexion "stale" typiques des
# bases serverless (Neon peut mettre en veille les connexions inactives).
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Session:

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
