from ipaddress import ip_address
import mongoengine as me
import datetime
from pkg_resources import require

from requests import request


class Submission(me.Document):
    meta = {"collection": "submissions"}

    type = me.StringField()
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateField(required=True, default=datetime.datetime.today)
    ended_date = me.DateField(required=True, default=datetime.datetime.today)

    owner = me.ReferenceField("User", dbref=True, required=True)
    remark = me.StringField()

    file = me.FileField()
    deadline = me.DateField(required=True, default=datetime.datetime.today)


class StudentWork(me.Document):
    meta = {"collection": "student_works"}

    remark = me.StringField()
    file = me.FileField()
    owner = me.ReferenceField("User", dbref=True, required=True)

    ip_address = me.StringField(required=True)

    submission = me.ReferenceField("Submission")
    class_ = me.ReferenceField("Class")
    project = me.ReferenceField("Projects")

    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
