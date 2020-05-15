'''
Created on Oct 13, 2013

@author: boatkrap
'''

from wtforms import validators
from wtforms import fields

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form

from .. import models


def validate_email(form, field):
    # user = models.User.objects(email=field.data).first()
    user = None
    if user is not None:
        raise validators.ValidationError(
                'This email: %s is available on system' % field.data)


def validate_username(form, field):

    if field.data.lower() in [
            'admin', 'administrator', 'lecturer', 'staff',
            'moderator', 'member', 'anonymous', 'pumbaa',
            'master', 'student', 'user', 'manager', 'coe',
            'teacher', 'psu']:
        raise validators.ValidationError(
                'This username: %s is not allowed' % field.data)

    user = None
    # user = models.User.objects(username=field.data).first()

    # request = get_current_request()
    # request_user = request.user
    # if request_user == user:
    #     return

    if user is not None:
        raise validators.ValidationError(
                'This user: %s is available on system' % field.data)


BaseProfileForm = model_form(
        models.User,
        FlaskForm,
        exclude=['created_date',
                 'updated_date',
                 'last_login_date',
                 'picture',
                 'roles',
                 'status',
                 'username',
                 'resources'],
        field_args={
            'title': {'label': 'Title'},
            'first_name': {'label': 'First Name'},
            'last_name': {'label': 'Last Name'},
            'title_th': {'label': 'Thai Title'},
            'first_name_th': {'label': 'Thai First Name'},
            'last_name_th': {'label': 'Thai Last Name'},
            'biography': {'label': 'Biography'},
            'email': {'label': 'Email'},
            }
        )


class ProfileForm(BaseProfileForm):
    pic = fields.FileField(
            'Picture',
            validators=[FileAllowed(['png', 'jpg'], 'allow png and jpg')]
            )
