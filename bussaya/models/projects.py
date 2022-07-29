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

    name = me.StringField(required=True, max_length=255)
    name_th = me.StringField(required=True, max_length=255)

    abstract = me.StringField(required=True)
    abstract_th = me.StringField(required=True)

    class_ = me.ReferenceField("Class", dbref=True)
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
            ("only name", "Only Name"),
            ("report", "Report"),
            ("presentation", "Presentation"),
            ("report presentation", "Report Presentation"),
        ],
    )

    committees_label_modifier = lambda c: f"{c.first_name} {c.last_name}"
    students_label_modifier = lambda s: f"{s.username} - {s.first_name} {s.last_name}"

    def get_opened_class(self):
        from .classes import Class

        student_ids = []
        if self.creator:
            student_ids.append(self.creator.username)
        for u in self.students:
            if u.username not in student_ids:
                student_ids.append(u.username)

        now = datetime.datetime.now()
        return Class.objects(
            started_date__lte=now, ended_date__gte=now, student_ids__in=student_ids
        ).first()

    def get_progress_reports(self):
        from .submissions import ProgressReport

        class_ = self.get_opened_class()
        return ProgressReport.objects(
            class_=class_,
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
