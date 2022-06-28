import mongoengine as me

import datetime
import humanize

SUBMISSION_TYPE = [("report", "Report"), ("presentation", "Presentation")]


class Submission(me.Document):
    meta = {"collection": "submissions", "strict": False}

    type = me.StringField(choices=SUBMISSION_TYPE)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateTimeField(required=True, default=datetime.datetime.today)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.today)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    owner = me.ReferenceField("User", dbref=True, required=True)
    description = me.StringField()

    file = me.FileField()

    def is_in_time(self):
        if self.started_date <= datetime.datetime.now() <= self.ended_date:
            return True

        if self.started_date > datetime.datetime.now():
            return "Upcoming"

        else:
            return False

    def set_remain_time(self):
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
        return self.started_date.strftime("%A, %d %B %Y, %I:%M %p")

    def natural_ended_date(self):
        return self.ended_date.strftime("%A, %d %B %Y, %I:%M %p")

    def get_student_work_by_owner(self, owner):
        student_works = StudentWork.objects.all().filter(submission=self, owner=owner)
        for student_work in student_works:
            return student_work


class StudentWork(me.Document):
    meta = {"collection": "student_works"}

    description = me.StringField()
    file = me.FileField()
    owner = me.ReferenceField("User", dbref=True, required=True)

    ip_address = me.StringField(required=True)

    submission = me.ReferenceField("Submission", dbref=True, required=True)
    class_ = me.ReferenceField("Class", dbref=True, required=True)
    project = me.ReferenceField("Projects")

    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
