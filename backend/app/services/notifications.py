from datetime import datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import NotificationLog, NotificationSetting


DEFAULT_CONTENT = {
    "meal_reminder": ("Rappel de repas", "C'est l'heure de votre repas."),
    "water_reminder": ("Rappel hydratation", "Pensez a boire de l'eau."),
    "training_reminder": ("Rappel entrainement", "Votre entrainement est bientot prevu."),
    "recovery_reminder": ("Rappel recuperation", "Prenez un moment pour recuperer."),
    "daily_goal": ("Objectif quotidien", "N'oubliez pas votre objectif du jour."),
    "meal_plan": ("Plan alimentaire", "Consultez votre prochain repas."),
    "progress_alert": ("Suivi de progression", "Votre suivi est pret a etre consulte."),
    "custom": ("Rappel personnalise", "Voici votre rappel personnalise."),
    "general": ("Rappel Fitapp", "Vous avez un nouveau rappel."),
}


def create_due_notifications(
    db: Session, at: datetime | None = None
) -> list[NotificationLog]:
    """Create at most one log per setting and calendar day."""
    current_time = at or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    current_time = current_time.astimezone(timezone.utc)

    settings = db.execute(
        select(NotificationSetting).where(
            NotificationSetting.is_enabled.is_(True),
            NotificationSetting.scheduled_time.is_not(None),
        )
    ).scalars().all()

    day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)
    created: list[NotificationLog] = []

    for setting in settings:
        if current_time.weekday() not in (setting.days_of_week or []):
            continue
        scheduled_time: time = setting.scheduled_time
        if (scheduled_time.hour, scheduled_time.minute) > (
            current_time.hour,
            current_time.minute,
        ):
            continue

        already_sent = db.execute(
            select(NotificationLog.id).where(
                NotificationLog.notification_setting_id == setting.id,
                NotificationLog.sent_at >= day_start,
                NotificationLog.sent_at <= day_end,
            )
        ).scalar_one_or_none()
        if already_sent is not None:
            continue

        notification_type = setting.notification_type.value
        default_title, default_body = DEFAULT_CONTENT[notification_type]
        created.append(
            NotificationLog(
                user_id=setting.user_id,
                notification_setting_id=setting.id,
                notification_type=setting.notification_type,
                title=setting.title or default_title,
                body=setting.body or default_body,
                language_code=setting.language_code,
            )
        )

    if created:
        db.add_all(created)
        db.commit()
        for notification in created:
            db.refresh(notification)

    return created