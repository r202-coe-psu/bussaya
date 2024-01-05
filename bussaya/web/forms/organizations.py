from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm
from wtforms import fields, widgets
from wtforms.fields import SelectField

from .fields import TagListField, TextListField

from bussaya import models

BaseOrganizationForm = model_form(
    models.Organization,
    FlaskForm,
    exclude=["created_date", "updated_date", "status", "creator", "last_updated_by"],
    field_args={
        "name": {"label": "Name"},
        "remark": {"label": "Remark"},
    },
)


class OrganizationForm(BaseOrganizationForm):
    pass


BaseMentorForm = model_form(
    models.Mentor,
    FlaskForm,
    exclude=["created_date", "updated_date"],
    field_args={
        "name": {"label": "Name"},
        "position": {"label": "Position"},
        "phone": {"label": "Phone"},
        "email": {"label": "Email"},
        "remark": {"label": "Remark"},
    },
)


class MentorForm(BaseMentorForm):
    pass
