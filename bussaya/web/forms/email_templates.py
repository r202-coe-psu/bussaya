from flask_wtf import FlaskForm
from wtforms import fields, validators


class EmailTemplateForm(FlaskForm):
    subject = fields.StringField("Subject", validators=[validators.DataRequired()])
    body = fields.TextAreaField(
        "Body", validators=[validators.DataRequired()], render_kw={"rows": 10}
    )
