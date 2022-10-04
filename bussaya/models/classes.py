import mongoengine as me
import datetime

from . import users

TYPE_CHOICE = [
    ("preproject", "Preproject"),
    ("project_1", "Project 1"),
    ("project_2", "Project 2"),
]


class Class(me.Document):
    meta = {"collection": "classes"}

    name = me.StringField(required=True, max_length=255)
    description = me.StringField()
    code = me.StringField(max_length=100)
    student_ids = me.ListField(me.StringField())

    tags = me.ListField(me.StringField(required=True))
    type = me.StringField(choices=TYPE_CHOICE)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateField(required=True, default=datetime.datetime.today)
    ended_date = me.DateField(required=True, default=datetime.datetime.today)

    owner = me.ReferenceField("User", dbref=True, required=True)

    def get_students(self):
        return users.User.objects(username__in=self.student_ids).order_by("username")

    def is_in_time(self):
        return self.started_date <= datetime.datetime.now().date() <= self.ended_date
