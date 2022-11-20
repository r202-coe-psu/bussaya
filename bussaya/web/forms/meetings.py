from wtforms import fields, widgets, Form, validators

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
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
        "title",
    ],
    field_args={
        "name": {"label": "Meeting Name"},
        "round": {"label": "Round"},
        "started_date": {"label": "Started Date", "format": "%Y-%m-%d %H:%M"},
        "ended_date": {"label": "Ended Date", "format": "%Y-%m-%d %H:%M"},
        "extended_date": {"label": "Extended Date", "format": "%Y-%m-%d %H:%M"},
    },
)


class MeetingForm(BaseMeetingForm):
    pass


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
        "late_reason",
    ],
    field_args={
        "project": {
            "label": "Project",
            "label_modifier": lambda p: p.name,
        },
        "title": {"label": "Title"},
        "description": {"label": "Desctription"},
        "remark": {"label": "Remark"},
        "advisors": {
            "label": "Advisors",
            "label_modifier": lambda l: l.get_fullname(),
        },
        "meeting_date": {
            "label": "Meeting Date",
            "format": "%d-%m-%Y",
            "widget": widgets.TextInput(),
        },
    },
)


class MeetingReportForm(BaseMeetingReportForm):
    uploaded_file = fields.FileField(
        "Upload File: PDF or PNG",
        validators=[FileAllowed(["pdf", "png"], "file extension not allow")],
    )


class LateMeetingReportForm(MeetingReportForm):
    late_reason = fields.StringField(
        "Late Reason",
        widget=widgets.TextArea(),
        validators=[validators.InputRequired()],
    )


class AdminMeetingReportForm(MeetingReportForm):
    student = fields.SelectField("Student")


class DisapproveForm(BaseMeetingReportForm):
    pass
