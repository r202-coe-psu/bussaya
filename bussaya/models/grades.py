from email.policy import default
from random import choices
import mongoengine as me
import datetime
import humanize

SEMESTER_TYPE = [("midterm", "Midterm"), ("final", "Final")]
RELEASE_STATUS = [("unreleased", "Unreleased"), ("released", "Released")]


class RoundGrade(me.Document):
    meta = {"collection": "round_grades"}

    type = me.StringField(choices=SEMESTER_TYPE)
    class_ = me.ReferenceField("Class", dbref=True, required=True)

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


STUDENT_GRADE_CHOICES = [
    ("-", "-"),
    ("A", "A"),
    ("B+", "B+"),
    ("B", "B"),
    ("C+", "C+"),
    ("C", "C"),
    ("D+", "D+"),
    ("D", "D"),
    ("E", "E"),
    ("I", "I"),
]


class Grader(me.EmbeddedDocument):
    lecturer = me.ReferenceField("User", dbref=True)
    mentor = me.ReferenceField("Mentor", dbref=True)


class StudentGrade(me.Document):
    meta = {"collection": "student_grades"}

    result = me.StringField(choices=STUDENT_GRADE_CHOICES, default="-")
    project = me.ReferenceField("Project", dbref=True)
    round_grade = me.ReferenceField("RoundGrade", dbref=True, required=True)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    grader = me.EmbeddedDocumentField(Grader)

    student = me.ReferenceField("User", dbref=True, required=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    def get_grader(self):
        if self.grader and self.grader.lecturer:
            return self.grader.lecturer
        elif self.grader and self.grader.mentor:
            return self.grader.mentor

        return None

    def get_result_choice(self):
        return StudentGrade.result.choices

    def get_grade_point(self):
        GRADE_POINTS = {
            "A": 4,
            "B+": 3.5,
            "B": 3,
            "C+": 2.5,
            "C": 2,
            "D+": 1.5,
            "D": 1,
            "E": 0.5,
        }
        return GRADE_POINTS[self.result.upper()]
