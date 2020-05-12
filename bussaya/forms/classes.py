from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm

from .fields import TagListField, TextListField

from bussaya import models

BaseClassForm = model_form(
        models.Class,
        FlaskForm,
        exclude=['created_date', 'updated_date', 'owner'],
        field_args={
            'name': {'label': 'Name'},
            'code': {'label': 'Code'},
            'description': {'label': 'Desctiption'},
            }
        )


class ClassForm(BaseClassForm):
    tags = TagListField('Tags')
    student_ids = TextListField('Student IDs')
