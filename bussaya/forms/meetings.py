from wtforms import fields, widgets, Form

from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
import mongoengine as me

from bussaya import models

BaseMeetingForm = model_form(
    models.Meeting,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "class_",
        "started_date",
        "ended_date",
        "title",
    ],
    field_args={
        "name": {"label": "Meeting Name"},
        "round": {"label": "Round"},
    },
)


class MeetingForm(BaseMeetingForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


BaseMeetingReportForm = model_form(
    models.MeetingReport,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "status",
        "ip_address",
        "class_",
        "meeting",
    ],
    field_args={
        "name": {"label": "Meeting Name"},
        "round": {"label": "Round"},
        "project": {
            "label": "Project",
            "label_modifier": lambda p: p.name,
        },
        "remark": {"label": "Disapprove Remark"},
    },
)


class MeetingReportForm(BaseMeetingReportForm):
    title = fields.StringField("Title")
    description = fields.TextAreaField("Description")
    meeting_date = fields.DateField("Meeting Date", format="%Y-%m-%d")


class DisapproveForm(BaseMeetingReportForm):
    pass
