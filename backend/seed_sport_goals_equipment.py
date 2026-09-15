"""
Execute les seeds Goal/SportGoalMatrix (app/services/sport_goal_seed_service.py)
et Equipment/Environment (app/services/equipment_seed_service.py).

Ces fonctions existaient deja dans le code mais n'etaient appelees par
aucun script ni aucune route : les tables Goal, SportGoalMatrix,
Equipment, Environment, SportEquipment, SportEnvironment restaient donc
vides en base, meme si les donnees etaient pretes cote code.

Usage :
    python seed_sport_goals_equipment.py

Idempotent (comme seed_sports.py) : peut etre relance sans creer de
doublons, verifie l'existant avant chaque insertion.
"""

from app.database.connection import SessionLocal
from app.services.equipment_seed_service import seed_equipment_and_environments
from app.services.sport_goal_seed_service import seed_goals_and_sport_goal_matrix


def main():
    db = SessionLocal()
    try:
        goals_result = seed_goals_and_sport_goal_matrix(db)
        equipment_result = seed_equipment_and_environments(db)

        print("=" * 60)
        print("SEED GOALS / SPORT_GOAL_MATRIX / EQUIPMENT / ENVIRONMENT TERMINE")
        print("=" * 60)
        print(f"Objectifs crees                : {goals_result['created_goals']}")
        print(f"Relations sport-objectif creees : {goals_result['created_mappings']}")
        print(f"Equipements crees               : {equipment_result['created_equipment']}")
        print(f"Environnements crees            : {equipment_result['created_environments']}")
        print(f"Relations sport-equipement crees: {equipment_result['created_sport_equipment']}")
        print(f"Relations sport-environnement   : {equipment_result['created_sport_environment']}")
        print("=" * 60)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
