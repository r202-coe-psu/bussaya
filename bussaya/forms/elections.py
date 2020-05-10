from wtforms import fields

from flask_wtf import FlaskForm


class ElectionForm(FlaskForm):
    started_date = fields.DateTimeField(
            'Start Date',
            format='%Y-%m-%d %H:%M')
    ended_date = fields.DateTimeField(
            'Update Date',
            format='%Y-%m-%d %H:%M')
