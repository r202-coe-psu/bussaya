from wtforms import fields
from wtforms import validators
from wtforms import widgets

from .fields import TagListField

from flask_wtf import FlaskForm


class ClassForm(FlaskForm):
    name = fields.StringField(
            'Name',
            validators=[validators.InputRequired(),
                        validators.Length(min=3)])
    description = fields.StringField(
            'Description',
            validators=[validators.InputRequired()],
            widget=widgets.TextArea())
    code = fields.StringField('Code')
    course = fields.SelectField(
            'Course',
            validators=[validators.InputRequired()])

    limited = fields.BooleanField('Limited Class', default=True)

    started_date = fields.DateField('Started Date', format='%d-%m-%Y')
    ended_date = fields.DateField('Ended Data', format='%d-%m-%Y')

    tags = TagListField(
            'Tags',
            validators=[validators.InputRequired(),
                        validators.Length(min=3)])
