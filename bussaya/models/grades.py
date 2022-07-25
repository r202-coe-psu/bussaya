from email.policy import default
from random import choices
import mongoengine as me
import datetime
import humanize

SEMESTER_TYPE = [("midterm", "Midterm"), ("final", "Final")]
RELEASE_STATUS = [("unreleased", "Unreleased"), ("released", "Released")]


class Grade(me.Document):
    meta = {"collection": "grades"}

    type = me.StringField(choices=SEMESTER_TYPE)
    class_ = me.ReferenceField("Class", dbref=True, required=True)
    student_ids = me.ListField()
    student_grades = me.ListField()

    release_status = me.StringField(choices=RELEASE_STATUS, default="unreleased")
    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    def is_in_time(self):
        if self.started_date <= datetime.datetime.now() <= self.ended_date:
            return True

        if self.started_date > datetime.datetime.now():
            return "Upcoming"

        else:
            return False

    def remain_time(self):
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


class StudentGrade(me.Document):
    meta = {"collection": "student_grades"}

    result = me.StringField(default="-")
    project = me.ReferenceField("Project", dbref=True)
    grade = me.ReferenceField("Grade", dbref=True, required=True)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    lecturer = me.ReferenceField("User", dbref=True, required=True)
    student = me.ReferenceField("User", dbref=True, required=True)

    def get_grade_point(self):
        if self.result == "A":
            return 4
        if self.result == "B+":
            return 3.5
        if self.result == "B":
            return 3
        if self.result == "C+":
            return 2.5
        if self.result == "C":
            return 2
        if self.result == "D+":
            return 1.5
        if self.result == "D":
            return 1
        if self.result == "E":
            return 0
