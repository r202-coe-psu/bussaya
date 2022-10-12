from wtforms import fields
from wtforms import validators
from wtforms import widgets

from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form

from bussaya import models

from .projects import BaseProjectForm
from .fields import TextListField


BaseGroupForm = model_form(
    models.Group,
    FlaskForm,
    exclude=["created_date", "class_", "committees", "students"],
    field_args={
        "name": {"label": "Name"},
    },
)


class GroupForm(BaseGroupForm):
    committees = fields.SelectMultipleField(
        "Committees",
        validators=[validators.InputRequired(), validators.length(max=5, min=1)],
    )
    students = TextListField("Student IDS")
