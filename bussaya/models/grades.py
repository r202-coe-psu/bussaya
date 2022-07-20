from email.policy import default
from random import choices
import mongoengine as me
import datetime

SEMESTER_TYPE = [("midterm", "Midterm"), ("final", "Final")]
# GRADE_SYSTEM_STATUS = [("opended", "Opended"), ("closed", "Closed")]


class Grade(me.Document):
    meta = {"collection": "grades"}

    type = me.StringField(choices=SEMESTER_TYPE)
    class_ = me.ReferenceField("Class", dbref=True, required=True)
    student_ids = me.ListField()
    student_grades = me.ListField()

    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )


class StudentGrade(me.Document):
    meta = {"collection": "student_grades"}

    result = me.StringField(default="-")
    project = me.ReferenceField("Project", dbref=True)
    grade = me.ReferenceField("Grade", dbref=True, required=True)

    class_ = me.ReferenceField("Class", dbref=True, required=True)
    teacher = me.ReferenceField("User", dbref=True, required=True)
    student = me.ReferenceField("User", dbref=True, required=True)
