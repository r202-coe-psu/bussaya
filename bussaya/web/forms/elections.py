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
            format='%Y-%m-%d %H:%M',
            widget=widgets.TextInput()
            )
    ended_date = fields.DateTimeField(
            'Update Date',
            widget=widgets.TextInput(),
            format='%Y-%m-%d %H:%M'
            )
