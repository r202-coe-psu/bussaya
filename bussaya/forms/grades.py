from wtforms import fields
from wtforms import widgets

from bussaya.forms.projects import BaseProjectForm

from .fields import TagListField

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form

from bussaya import models

BaseProjectForm = model_form(
    models.Grade,
    FlaskForm,
    exclude=[
        "type" "class_",
        "student_ids",
        "student_grades",
        "started_date",
        "ended_date",
        "created_date",
        "updated_date",
    ],
    field_args={
        "type": {"label": "Type"},
        "description": {"label": "Description"},
    },
)


class GradeForm(BaseProjectForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
