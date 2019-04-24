from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets
from wtforms.fields import html5

from .fields import TagListField, TextListField

from flask_wtf import FlaskForm

class ElectionForm(FlaskForm):
    started_date = fields.DateTimeField(
            'Start Date',
            format='%Y-%m-%d %H:%M')
    ended_date = fields.DateTimeField(
            'Update Date',
            format='%Y-%m-%d %H:%M')

