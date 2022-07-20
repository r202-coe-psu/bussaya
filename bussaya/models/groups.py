import mongoengine as me
import datetime


class Group(me.Document):
    meta = {"collection": "groups"}

    name = me.StringField(required=True, max_length=255)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    committees = me.ListField(me.ReferenceField("User", dbref=True))
    students = me.ListField(me.ReferenceField("User", dbref=True))

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
