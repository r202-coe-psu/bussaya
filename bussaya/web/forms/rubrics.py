from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm
from wtforms import fields, validators

from bussaya import models

BaseRubricTemplateForm = model_form(
    models.RubricTemplate,
    FlaskForm,
    only=["name", "curriculum", "class_type", "description"],
    field_args={
        "name": {"label": "Name"},
        "curriculum": {"label": "Curriculum", "label_modifier": lambda c: c.name},
        "class_type": {"label": "Class Type"},
        "description": {"label": "Description"},
    },
)


class RubricTemplateForm(BaseRubricTemplateForm):
    pass


class RubricCriterionForm(FlaskForm):
    name = fields.StringField("Name", validators=[validators.DataRequired()])
    description = fields.TextAreaField("Description", validators=[validators.Optional()])
    max_score = fields.FloatField(
        "Max Score", validators=[validators.DataRequired(), validators.NumberRange(min=0)]
    )
    clos = fields.SelectMultipleField("CLOs", validators=[validators.Optional()])
