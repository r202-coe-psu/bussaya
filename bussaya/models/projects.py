import mongoengine as me
import datetime

class Project(me.Document):
    meta = {'collection': 'projects'}

    name = me.StringField(required=True)
    description = me.StringField()
    class_ = me.ReferenceField('Class', dbref=True, required=True)
    tags = me.ListField(me.StringField())

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    student_ids = me.ListField(me.StringField(required=True))

    owners = me.ListField(me.ReferenceField('User', dbref=True))
    advisor = me.ReferenceField('User', dbref=True)
