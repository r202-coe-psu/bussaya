from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm
from wtforms import fields, validators

from bussaya import models

class RubricTemplateForm(FlaskForm):
    name = fields.StringField("Name", validators=[validators.DataRequired()])
    curriculums = fields.SelectMultipleField(
        "Curriculums", validators=[validators.DataRequired()]
    )
    class_type = fields.SelectField(
        "Class Type",
        choices=models.classes.TYPE_CHOICE,
        validators=[validators.DataRequired()],
    )
    description = fields.TextAreaField(
        "Description", validators=[validators.Optional()]
    )


LEVEL_FIELD_MAP = [
    ("A", "level_A"),
    ("B+", "level_B_plus"),
    ("B", "level_B"),
    ("C+", "level_C_plus"),
    ("C", "level_C"),
    ("D+", "level_D_plus"),
    ("D", "level_D"),
    ("E", "level_E"),
    ("I", "level_I"),
    ("W", "level_W"),
]


class RubricCriterionForm(FlaskForm):
    name = fields.StringField("Name", validators=[validators.DataRequired()])
    description = fields.TextAreaField("Description", validators=[validators.Optional()])
    max_score = fields.FloatField(
        "Max Score", validators=[validators.DataRequired(), validators.NumberRange(min=0)]
    )
    clos = fields.SelectMultipleField("CLOs", validators=[validators.Optional()])

    level_A = fields.TextAreaField("Grade A Explanation", validators=[validators.Optional()])
    level_B_plus = fields.TextAreaField("Grade B+ Explanation", validators=[validators.Optional()])
    level_B = fields.TextAreaField("Grade B Explanation", validators=[validators.Optional()])
    level_C_plus = fields.TextAreaField("Grade C+ Explanation", validators=[validators.Optional()])
    level_C = fields.TextAreaField("Grade C Explanation", validators=[validators.Optional()])
    level_D_plus = fields.TextAreaField("Grade D+ Explanation", validators=[validators.Optional()])
    level_D = fields.TextAreaField("Grade D Explanation", validators=[validators.Optional()])
    level_E = fields.TextAreaField("Grade E Explanation", validators=[validators.Optional()])
    level_I = fields.TextAreaField("Grade I Explanation", validators=[validators.Optional()])
    level_W = fields.TextAreaField("Grade W Explanation", validators=[validators.Optional()])

