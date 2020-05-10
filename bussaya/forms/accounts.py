'''
Created on Oct 13, 2013

@author: boatkrap
'''

from wtforms import validators


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
