from wtforms import fields
from wtforms import validators
from wtforms import widgets
from .fields import TagListField

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form

from bussaya import models

BaseSubmissionForm = model_form(
    models.Submission,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "class_",
        "ip_address",
        "started_date",
        "ended_date",
    ],
    field_args={
        "type": {"label": "Type"},
        "round": {"label": "Round"},
        "description": {"label": "Description"},
    },
)


class SubmissionForm(BaseSubmissionForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    extended_date = fields.DateTimeField(
        "Extended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


BaseProgressReportForm = model_form(
    models.ProgressReport,
    FlaskForm,
    exclude=[],
    only=["project", "description"],
    field_args={
        "project": dict(label="Project", label_modifier=lambda p: p.name),
        "description": dict(label="Description"),
    },
)


class ProgressReportForm(BaseProgressReportForm):
    uploaded_file = fields.FileField(
        "Upload File: PDF only", validators=[FileAllowed(["pdf"], "PDF only")]
    )
