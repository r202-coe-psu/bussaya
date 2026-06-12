from wtforms import fields
from wtforms import widgets
from wtforms import validators

from flask_wtf import FlaskForm


class ElectionForm(FlaskForm):
    class_ = fields.SelectField(
            'Class',
            validators=[validators.InputRequired()]
            )
    started_date = fields.DateTimeField(
            'Start Date',
            format=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
            widget=widgets.DateTimeLocalInput()
            )
    ended_date = fields.DateTimeField(
            'Update Date',
            widget=widgets.DateTimeLocalInput(),
            format=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']
            )
