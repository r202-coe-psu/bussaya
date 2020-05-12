from wtforms import fields
from wtforms import validators
from wtforms import widgets

from .fields import TagListField, TextListField

from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form


from bussaya import models

BaseProjectForm = model_form(
        models.Project,
        FlaskForm,
        exclude=['created_date', 'updated_date', 'owner', 'approvals',
                 'resources', 'students', 'advisor', 'committees'],
        field_args={
            'name': {'label': 'Name', 'widget': widgets.TextInput()},
            'name_th': {'label': 'Thai Name', 'widget': widgets.TextInput()},
            'abstract': {'label': 'Abstract'},
            'abstract_th': {'label': 'Thai Abstract'},
            'public': {'label': 'Public'},
            }
        )


class ProjectForm(BaseProjectForm):
    tags = TagListField('Tags')
    class_ = fields.SelectField(
            'Class',
            validators=[validators.InputRequired()]
            )
    contributors = fields.SelectField(
            'Contributors',
            default=None,
            choices=[('', 'If your project has contributor')]
            )
    advisor = fields.SelectField(
            'Advisor',
            validators=[validators.InputRequired()]
            )

    committees = fields.SelectMultipleField(
            'Committees',
            validators=[validators.InputRequired(),
                        validators.length(max=5, min=1)]
            )

class ProjectUploadForm(FlaskForm):
    pass
