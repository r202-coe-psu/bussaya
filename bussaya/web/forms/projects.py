from wtforms import fields
from wtforms import validators
from wtforms import widgets

from .fields import TagListField

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form


from bussaya import models

BaseProjectForm = model_form(
    models.Project,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "approvals",
        "resources",
        "class_",
    ],
    field_args={
        "name": {"label": "English Name"},
        "name_th": {"label": "Thai Name"},
        "abstract": {"label": "English Abstract"},
        "abstract_th": {"label": "Thai Abstract"},
        "advisors": {
            "label": "Project Advisor",
            "label_modifier": lambda a: f"{a.first_name} {a.last_name}",
        },
        "committees": {
            "label": "Committees",
            "allow_blank": True,
            "blank_text": "There are no committees",
            "label_modifier": lambda a: f"{a.first_name} {a.last_name}",
        },
        "students": {
            "label": "Contributors",
            "allow_blank": True,
            "blank_text": "There are no contributors",
            "label_modifier": lambda s: f"{s.first_name} {s.last_name}",
        },
        "public": {
            "label": "Public",
        },
    },
)


class ProjectForm(BaseProjectForm):
    tags = TagListField(
        "Tags: divied by comma (,)", validators=[validators.length(min=3)]
    )
