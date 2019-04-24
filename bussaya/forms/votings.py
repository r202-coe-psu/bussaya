from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets
from wtforms.fields import html5

from .fields import TagListField, TextListField

from flask_wtf import FlaskForm

class VotingForm(FlaskForm):
    projects = fields.SelectMultipleField(
            'Projects',
            validators=[validators.InputRequired(),
                        validators.length(max=3, min=1)])
