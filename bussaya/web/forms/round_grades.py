from wtforms import fields, widgets, Form, validators

from .projects import BaseProjectForm

from .fields import TagListField

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form

from bussaya import models

BaseRoundGradeForm = model_form(
    models.RoundGrade,
    FlaskForm,
    exclude=[
        "type",
        "class_",
        "student_ids",
        "student_grades",
        "started_date",
        "ended_date",
        "created_date",
        "updated_date",
    ],
)


class RoundGradeForm(BaseRoundGradeForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format=["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format=["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]
    )


class CriterionScoreForm(Form):
    criterion_id = fields.HiddenField()
    score = fields.FloatField(validators=[validators.Optional()])


class RubricGradingEntryForm(Form):
    student_id = fields.HiddenField()
    criterion_scores = fields.FieldList(fields.FormField(CriterionScoreForm))


class MentorRubricGradingEntryForm(RubricGradingEntryForm):
    mentor_id = fields.SelectField("Mentor", validators=[validators.Optional()])


class GroupRubricGradingForm(FlaskForm):
    gradings = fields.FieldList(fields.FormField(RubricGradingEntryForm))


class GroupMentorRubricGradingForm(FlaskForm):
    gradings = fields.FieldList(fields.FormField(MentorRubricGradingEntryForm))
