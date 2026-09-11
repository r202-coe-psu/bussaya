import datetime
import mongoengine as me

DEADLINE_TARGET_TYPE = [
    ("round_grade", "Round Grade"),
    ("meeting", "Meeting Report"),
    ("report", "Report"),
    ("presentation", "Presentation"),
]


class DeadlineNotification(me.Document):
    """Tracks a single deadline-reminder email so the reminder job stays
    idempotent across repeated/cron-scheduled runs."""

    meta = {
        "collection": "deadline_notifications",
        "indexes": [
            {
                "fields": ["target_type", "target_id", "recipient", "days_before"],
                "unique": True,
            }
        ],
    }

    target_type = me.StringField(required=True, choices=DEADLINE_TARGET_TYPE)
    target_id = me.ObjectIdField(required=True)
    recipient = me.ReferenceField("User", dbref=True, required=True)
    days_before = me.IntField(required=True)

    status = me.StringField(required=True, default="sent", choices=["sent", "failed"])
    sent_date = me.DateTimeField(required=True, default=datetime.datetime.now)
