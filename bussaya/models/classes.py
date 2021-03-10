import mongoengine as me
import datetime


class Class(me.Document):
    meta = {'collection': 'classes'}

    name = me.StringField(required=True, max_length=255)
    description = me.StringField()
    code = me.StringField(max_length=100)
    student_ids = me.ListField(me.StringField())

    tags = me.ListField(me.StringField(required=True))

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    started_date = me.DateField(required=True,
                                default=datetime.datetime.today)

    ended_date = me.DateField(required=True,
                              default=datetime.datetime.today)

    owner = me.ReferenceField('User', dbref=True, required=True)
