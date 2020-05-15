import mongoengine as me
import datetime

from flask_login import UserMixin
from flask import url_for

from .projects import Project


class User(me.Document, UserMixin):
    username = me.StringField(required=True, unique=True)

    title = me.StringField(max_length=50)
    email = me.StringField(required=True, unique=True, max_length=200)
    first_name = me.StringField(required=True, max_length=200)
    last_name = me.StringField(required=True, max_length=200)

    title_th = me.StringField(max_length=50)
    first_name_th = me.StringField(max_length=200)
    last_name_th = me.StringField(max_length=200)

    biography = me.StringField()

    picture = me.ImageField(thumbnail_size=(800, 600, True))

    status = me.StringField(required=True, default='disactive')
    roles = me.ListField(me.StringField(), default=['user'])

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    last_login_date = me.DateTimeField(required=True,
                                       default=datetime.datetime.now,
                                       auto_now=True)

    resources = me.DictField()

    meta = {'collection': 'users',
            'strict': False}

    def has_roles(self, roles):
        for role in roles:
            if role in self.roles:
                return True
        return False

    def get_picture(self):
        if self.picture:
            return url_for('accounts.picture', user_id=self.id, filename=self.picture.filename)
        if 'google' in self.resources:
            return self.resources['google'].get('picture', '')
        return url_for('static', filename='images/user.png')

    def get_project(self):
        project = Project.objects(students=self).order_by('-id').first()
        return project

    def get_advisee_projects(self):
        projects = Project.objects(advisor=self)
        return projects
