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
        exclude=['created_date', 'updated_date', 'owner'],
        field_args={
            'type': {'label': 'Type'},
            'remark': {'label': 'Remark'},
            'started_date': {'label': 'Start Date', 'format': '%Y-%m-%d'},
            'ended_date': {'label': 'End Date', 'format': '%Y-%m-%d'},
            }
        )
class SubmissionForm(BaseProjectForm):
    pass


class StudentWorkForm(BaseProjectForm):
    file = fields.FileField(validators=[FileAllowed(['pdf'], 'PDF only')])