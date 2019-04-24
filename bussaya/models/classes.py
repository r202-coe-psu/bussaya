import mongoengine as me
import datetime


class Class(me.Document):
    meta = {'collection': 'classes'}

    name = me.StringField(required=True)
    description = me.StringField(required=True)
    code = me.StringField()

    tags = me.ListField(me.StringField(required=True))

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    started_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)

    ended_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)

    owner = me.ReferenceField('User', dbref=True, required=True)
