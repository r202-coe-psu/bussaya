import mongoengine as me
import datetime

from bson.objectid import ObjectId


class ProjectResource(me.EmbeddedDocument):
    id = me.ObjectIdField(required=True, default=ObjectId)
    data = me.FileField()
    link = me.StringField()
    type = me.StringField(
        required=True,
        choices=[
            "report",
            "similarity",
            "presentation",
            "poster",
            "other",
            "video",
            "git",
        ],
    )
    status = me.StringField(required=True, default="active")
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )


class ProjectApproval(me.EmbeddedDocument):
    id = me.ObjectIdField(required=True, default=ObjectId())
    committee = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    comment = me.StringField()
    type = me.StringField()


class Project(me.Document):
    meta = {
        "collection": "projects",
        "strict": False,
    }

    name = me.StringField(required=True)
    name_th = me.StringField(required=True)

    abstract = me.StringField(required=True)
    abstract_th = me.StringField(required=True)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    tags = me.ListField(me.StringField())

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    students = me.ListField(me.ReferenceField("User", dbref=True))
    creator = me.ReferenceField("User", dbref=True)

    advisor = me.ReferenceField("User", dbref=True)
    committees = me.ListField(me.ReferenceField("User", dbref=True))
    approvals = me.ListField(me.EmbeddedDocumentField(ProjectApproval))

    resources = me.ListField(me.EmbeddedDocumentField(ProjectResource))

    public = me.StringField(
        required=True,
        default="only name",
        choices=[
            "report",
            "presentation",
            "report presentation",
        ],
    )

    def get_resource(self, type_):
        resources = reversed(self.resources)
        for r in resources:
            if r.type == type_:
                return r

        return None

    def is_approval(self, user):
        for approval in self.approvals:
            if user == approval.committee:
                return True

        return False

    def is_advisor_approval(self):
        for approval in self.approvals:
            if approval.committee == self.advisor:
                if approval.type == "approve":
                    return True

        return False
