from wtforms import fields
from wtforms import validators
from wtforms import widgets

from bussaya.forms.projects import BaseProjectForm

from flask_wtf import FlaskForm
from .fields import TextListField
from flask_mongoengine.wtf import model_form

from bussaya import models

BaseProjectForm = model_form(
    models.Group,
    FlaskForm,
    exclude=["created_date", "class_", "lecturer", "students"],
    field_args={
        "name": {"label": "Name"},
    },
)


class GroupForm(BaseProjectForm):
    lecturer = fields.SelectField("Lecturer", validators=[validators.InputRequired()])
    students = TextListField("Student IDS")
