from wtforms import fields
from wtforms import validators
from wtforms import widgets

from bussaya.forms.projects import BaseProjectForm

from .fields import TagListField

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form

from bussaya import models

BaseProjectForm = model_form(
    models.Submission,
    FlaskForm,
    exclude=["created_date", "updated_date", "owner"],
    field_args={
        "type": {"label": "Type"},
        "remark": {"label": "Remark"},
    },
)


class SubmissionForm(BaseProjectForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


class StudentWorkForm(BaseProjectForm):
    file = fields.FileField(validators=[FileAllowed(["pdf"], "PDF only")])
