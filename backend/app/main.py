import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import foods
from app.routes import (
    assistant,
    db,
    hydration,
    inventory,
    languages,
    lifestyle,
    meal_analysis,
    notifications,
    onboarding,
    profile,
    recipes,
    sport,
    users,
    nutrition,
    nutrition_tracking,
)

load_dotenv()

app = FastAPI(
    title="Fitapp API",
    description="Backend de l'application Fitapp",
    version="1.0.0",
)
app.include_router(foods.router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(languages.router)
app.include_router(db.router)
app.include_router(users.router)
app.include_router(onboarding.router)
app.include_router(profile.router)
app.include_router(nutrition.router)
app.include_router(hydration.router)
app.include_router(inventory.router)
app.include_router(recipes.router)
app.include_router(notifications.router)
app.include_router(nutrition_tracking.router)
app.include_router(sport.router)
app.include_router(lifestyle.router)
app.include_router(meal_analysis.router, prefix="/api/v1")
app.include_router(assistant.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "ok", "service": "fitapp-api"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
