from flask_mongoengine.wtf import model_form
from flask_mongoengine.wtf.fields import ModelSelectMultipleField
from flask_wtf import FlaskForm
from wtforms import fields, widgets
from wtforms.fields import SelectField

from .fields import TagListField, TextListField

from bussaya import models

BaseClassForm = model_form(
    models.Class,
    FlaskForm,
    exclude=["created_date", "updated_date", "owner", "curriculums"],
    field_args={
        "name": {"label": "Name"},
        "code": {"label": "Code"},
        "description": {"label": "Desctiption"},
        "type": {"label": "Type"},
        "started_date": {
            "label": "Start Date",
            "format": "%Y-%m-%d",
            "widget": widgets.TextInput(),
        },
        "ended_date": {
            "label": "End Date",
            "format": "%Y-%m-%d",
            "widget": widgets.TextInput(),
        },
    },
)


class ClassForm(BaseClassForm):
    tags = TagListField("Tags")
    student_ids = TextListField("Student IDs", render_kw={"rows": 5})
    curriculums = ModelSelectMultipleField(
        "Curriculums",
        model=models.Curriculum,
        label_modifier=lambda c: c.name,
        allow_blank=True,
        blank_text="No curriculum",
    )
