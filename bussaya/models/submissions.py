from email.policy import default
import resource
from telnetlib import STATUS
import mongoengine as me
import gridfs

import datetime
import humanize

SUBMISSION_TYPE = [("report", "Report"), ("presentation", "Presentation")]

APPROVAL_STATUS = [
    ("approved", "Approved"),
    ("disapproved", "Disapproved"),
    ("wait", "Wait"),
    ("late-report", "Late Report"),
]


class Submission(me.Document):
    meta = {"collection": "submissions", "strict": False}

    type = me.StringField(choices=SUBMISSION_TYPE)
    description = me.StringField()
    round = me.StringField(
        choices=[("midterm", "Midterm"), ("final", "Final")], required=True
    )

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateTimeField(required=True, default=datetime.datetime.today)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.today)
    extended_date = me.DateTimeField(required=True, default=datetime.datetime.today)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    owner = me.ReferenceField("User", dbref=True, required=True)

    def get_status(self):
        now = datetime.datetime.now()
        if self.started_date > now:
            return "upcoming"

        elif self.started_date <= now <= self.ended_date:
            return "opened"

        elif self.ended_date <= now <= self.extended_date:
            return "lated"

        else:
            return "closed"

    def get_remain_time(self):
        now = datetime.datetime.now()
        start = self.started_date
        end = self.ended_date
        extend = self.extended_date

        if start > now:
            delta = start - now
            return (
                delta.days,
                f"Opening in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )

        elif now > end and extend > now:
            delta = extend - now
            return (
                delta.days,
                f"Closing in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )

        elif now > start and end > now:
            delta = end - now
            return (
                delta.days,
                f"Due in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )

        return (extend - now).days, "Out of time"

    def natural_started_date(self):
        return self.started_date.strftime("%d %B %Y, %I:%M %p")

    def natural_ended_date(self):
        return self.ended_date.strftime("%d %B %Y, %I:%M %p")

    def natural_extended_date(self):
        return self.extended_date.strftime("%d %B %Y, %I:%M %p")

    def get_progress_report_by_owner(self, owner):
        progress_reports = ProgressReport.objects.all().filter(
            submission=self, owner=owner
        )
        for progress_report in progress_reports:
            return progress_report


class Meeting(me.Document):
    meta = {"collection": "meetings"}

    name = me.StringField(max_length=255)
    round = me.StringField(
        choices=[("midterm", "Midterm"), ("final", "Final")], required=True
    )

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateTimeField(required=True, default=datetime.datetime.today)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.today)
    extended_date = me.DateTimeField(required=True, default=datetime.datetime.today)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    owner = me.ReferenceField("User", dbref=True, required=True)

    def get_status(self):
        if self.started_date > datetime.datetime.now():
            return "upcoming"

        elif self.started_date <= datetime.datetime.now() <= self.ended_date:
            return "opened"

        elif self.ended_date <= datetime.datetime.now() <= self.extended_date:
            return "lated"

        return "closed"

    def get_remain_time(self):
        now = datetime.datetime.now()
        start = self.started_date
        end = self.ended_date

        if start > now:
            delta = start - now
            return (
                delta.days,
                f"Opening in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )
        if now > end:
            return (end - now).days, "Out of time"

        if now > start and end > now:
            delta = end - now
            return (
                delta.days,
                f"Closing in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )

    def natural_started_date(self):
        return self.started_date.strftime("%d %B %Y, %I:%M %p")

    def natural_ended_date(self):
        return self.ended_date.strftime("%d %B %Y, %I:%M %p")

    def get_meeting_report_by_owner(self, owner):
        meeting_reports = MeetingReport.objects.all().filter(meeting=self, owner=owner)
        for meeting_report in meeting_reports:
            return meeting_report


class ProgressReport(me.Document):
    meta = {"collection": "progress_reports"}

    submission = me.ReferenceField("Submission", dbref=True)

    owner = me.ReferenceField("User", dbref=True, required=True)
    class_ = me.ReferenceField("Class", dbref=True, required=True)
    project = me.ReferenceField("Project", dbref=True, required=True)
    ip_address = me.StringField(required=True)

    description = me.StringField()
    remark = me.StringField(default="")
    file = me.FileField(
        collection_name="progress_report_fs",
    )

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    def get_uploaded_date(self):
        return self.updated_date.strftime("%d %B %Y, %H:%M:%S")
    
    def get_file_content(self):
        """ดึงเนื้อหาของไฟล์จาก progress_report_fs โดยใช้ file_id"""
        return self.file.read()


class MeetingReport(me.Document):
    meta = {"collection": "meeting_reports"}

    meeting = me.ReferenceField("Meeting", dbref=True)

    owner = me.ReferenceField("User", dbref=True, required=True)
    class_ = me.ReferenceField("Class", dbref=True, required=True)
    project = me.ReferenceField("Project", dbref=True, required=True)
    ip_address = me.StringField(required=True, max_length=255)

    title = me.StringField(max_length=255, required=True)
    description = me.StringField()
    meeting_date = me.DateField(default=datetime.datetime.today)
    late_reason = me.StringField(default="")

    status = me.StringField(choices=APPROVAL_STATUS)
    remark = me.StringField(default="")

    advisors = me.ListField(me.ReferenceField("User", dbref=True))

    approver = me.ReferenceField("User", dbref=True)
    approver_ip_address = me.StringField(max_length=255)
    approved_date = me.DateTimeField()

    file = me.FileField(
        collection_name="meeting_fs",
    )

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    advisors_label_modifier = lambda a: a.fullname


class FinalSubmission(me.Document):
    meta = {"collection": "final_submissions", "strict": False}

    description = me.StringField()

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateTimeField(required=True, default=datetime.datetime.today)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.today)
    extended_date = me.DateTimeField(required=True, default=datetime.datetime.today)

    class_ = me.ReferenceField("Class", dbref=True, required=True)

    def get_status(self):
        if self.started_date > datetime.datetime.now():
            return "upcoming"

        if self.started_date <= datetime.datetime.now() <= self.ended_date:
            return "opened"

        if self.ended_date <= datetime.datetime.now() <= self.extended_date:
            return "lated"

        else:
            return "closed"

    def get_remain_time(self):
        now = datetime.datetime.now()
        start = self.started_date
        end = self.ended_date
        extend = self.extended_date

        if start > now:
            delta = start - now
            return (
                delta.days,
                f"Opening in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )

        if now > end and extend > now:
            delta = extend - now
            return (
                delta.days,
                f"Closing in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )

        if now > start and end > now:
            delta = end - now
            return (
                delta.days,
                f"Due in {humanize.naturaltime(delta).removesuffix(' ago')}",
            )

        else:
            return (extend - now).days, "Out of time"

    def natural_started_date(self):
        return self.started_date.strftime("%d %B %Y, %I:%M %p")

    def natural_ended_date(self):
        return self.ended_date.strftime("%d %B %Y, %I:%M %p")

    def natural_extended_date(self):
        return self.extended_date.strftime("%d %B %Y, %I:%M %p")


class FinalReport(me.Document):
    meta = {
        "collection": "final_reports",
        "strict": False,
    }

    final_submission = me.ReferenceField("FinalSubmission", required=True, dbref=True)

    owner = me.ReferenceField("User", dbref=True)
    project = me.ReferenceField("Project", required=True, dbref=True)
    ip_address = me.StringField(required=True, max_length=255)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    def natural_updated_date(self):
        return self.updated_date.strftime("%d %B %Y, %I:%M %p")
