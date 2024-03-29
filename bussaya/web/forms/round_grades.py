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
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


BaseStudentGradeForm = model_form(
    models.StudentGrade,
    Form,
    only=["result"],
    field_args={
        "result": {"label": ""},
    },
)


class GradingForm(BaseStudentGradeForm):
    student_id = fields.HiddenField()


class MentorGradingForm(GradingForm):
    mentor_id = fields.SelectField("Mentor", validators=[validators.Optional()])


class GroupGradingForm(FlaskForm):
    gradings = fields.FieldList(fields.FormField(GradingForm))


class GroupMentorGradingForm(FlaskForm):
    gradings = fields.FieldList(fields.FormField(MentorGradingForm))
