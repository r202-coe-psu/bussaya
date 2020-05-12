from wtforms import fields
from wtforms import validators
from wtforms import widgets

from .fields import TagListField, TextListField

from flask_wtf.form import _Auto
from flask_mongoengine.wtf import model_form


from bussaya import models

# class ClassForm(FlaskForm):
#     name = fields.StringField(
#             'Name',
#             validators=[validators.InputRequired(),
#                         validators.Length(min=3)])
#     description = fields.StringField(
#             'Description',
#             validators=[validators.InputRequired()],
#             widget=widgets.TextArea())
#     code = fields.StringField('Code')
#     course = fields.SelectField(
#             'Course',
#             validators=[validators.InputRequired()])

#     limited = fields.BooleanField('Limited Class', default=True)

#     started_date = fields.DateField('Started Date', format='%d-%m-%Y')
#     ended_date = fields.DateField('Ended Data', format='%d-%m-%Y')

#     tags = TagListField(
#             'Tags',
#             validators=[validators.InputRequired(),
#                         validators.Length(min=3)])

BaseClassForm = model_form(
        models.Class,
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

    def __init__(self, formdata=_Auto, **kwargs):
        super().__init__(formdata=formdata, **kwargs)

