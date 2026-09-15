

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import engine, get_db

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/health")
def database_health():
    """
    Verifie que Neon repond.

    Ouvre une vraie connexion, execute SELECT 1 et renvoie quelques
    metadonnees utiles (version du serveur, base courante, utilisateur).
    """
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar_one()
            db_name = conn.execute(text("SELECT current_database()")).scalar_one()
            db_user = conn.execute(text("SELECT current_user")).scalar_one()
    except Exception as exc:  # pragma: no cover - depends on Neon state
        raise HTTPException(
            status_code=503,
            detail=f"Base de donnees injoignable : {exc}",
        )

    return {
        "status": "ok",
        "database": db_name,
        "user": db_user,
        "version": version.split(",")[0],
    }


@router.get("/ping")
def database_ping(db: Session = Depends(get_db)):
    """Variante legere qui passe par la session FastAPI (Depends(get_db))."""
    result = db.execute(text("SELECT 1")).scalar_one()
    return {"status": "ok", "select_1": result}
