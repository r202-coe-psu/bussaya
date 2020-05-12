import mongoengine as me
import datetime


class Resource(me.EmbeddedDocument):
    data = me.FileField()
    file_type = me.StringField()
    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)


class Approval(me.EmbeddedDocument):
    committee = me.ReferenceField('User', dbref=True)

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    comment = me.StringField()
    type = me.StringField()


class Project(me.Document):
    meta = {'collection': 'projects'}

    name = me.StringField(required=True)
    name_th = me.StringField(required=True)

    abstract = me.StringField(required=True)
    abstract_th = me.StringField(required=True)

    class_ = me.ReferenceField('Class', dbref=True, required=True)
    tags = me.ListField(me.StringField())


    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    students = me.ListField(me.ReferenceField('User', dbref=True))
    creator = me.ReferenceField('User', dbref=True)

    advisor = me.ReferenceField('User', dbref=True)
    committees = me.ListField(me.ReferenceField('User', dbref=True))
    approvals = me.ListField(me.EmbeddedDocumentField(Approval))

    resources = me.ListField(me.EmbeddedDocumentField(Resource))

    public = me.StringField(
            required=True,
            default='only name',
            choices=['private',
                     'only name',
                     'abstract',
                     'report'])

