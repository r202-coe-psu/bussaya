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

    description = me.StringField()

    class_ = me.ReferenceField('Class', dbref=True, required=True)
    tags = me.ListField(me.StringField())

    public = me.StringField()

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    student_ids = me.ListField(me.StringField(required=True))
    students = me.ListField(me.ReferenceField('User', dbref=True))

    advisor = me.ReferenceField('User', dbref=True)
    committees = me.ListField(me.ReferenceField('User', dbref=True))
    approvals = me.ListField(me.EmbeddedDocumentField(Approval))

    resources = me.ListField(me.EmbeddedDocumentField(Resource))

