import mongoengine as me
import datetime


class Voting(me.Document):
    meta = {'collection': 'votings'}

    user = me.ReferenceField('User', dbref=True, required=True)
    projects = me.ListField(
            me.ReferenceField('Project', dbref=True, required=True))
    class_ = me.ReferenceField('Class', dbref=True, required=True)
    election = me.ReferenceField('Election', dbref=True, required=True)

    raw_voting_projects = me.ListField(me.StringField())

    voted_date = me.DateTimeField(required=True,
                                  default=datetime.datetime.now)


class Election(me.Document):
    meta = {'collection': 'elections'}

    owner = me.ReferenceField('User', dbref=True, required=True)
    class_ = me.ReferenceField('Class', dbref=True, required=True)

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)

    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    started_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    ended_date = me.DateTimeField(required=True,
                                  default=datetime.datetime.now)
