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
        "started_date": {
            "label": "Started Date",
            "format": "%Y-%m-%d %H:%M",
            "widget": widgets.TextInput(),
        },
        "ended_date": {
            "label": "Ended Date",
            "format": "%Y-%m-%d %H:%M",
            "widget": widgets.TextInput(),
        },
        "extended_date": {
            "label": "Extended Date",
            "format": "%Y-%m-%d %H:%M",
            "widget": widgets.TextInput(),
        },
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
        "approved_date",
        "approver_ip_address",
    ],
    field_args={
        "project": {
            "label": "Project",
            "label_modifier": lambda p: f"{p.name} - {''.join([s.username + ' ' + s.get_fullname() + ' ' for s in p.students])}",
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
            "format": "%Y-%m-%d",
            "widget": widgets.TextInput(),
        },
    },
)


class MeetingReportForm(BaseMeetingReportForm):
    uploaded_file = fields.FileField(
        "Upload File: PDF or PNG",
        validators=[
            FileAllowed(
                ["pdf", "png", "jpg", "jpeg", "webp"], "file extension not allow"
            )
        ],
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
