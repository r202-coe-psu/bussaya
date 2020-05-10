from wtforms import fields
from wtforms import validators

from flask_wtf import FlaskForm


class VotingForm(FlaskForm):
    projects = fields.SelectMultipleField(
            'Projects',
            validators=[validators.InputRequired(),
                        validators.length(max=3, min=1)])
