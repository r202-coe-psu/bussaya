from email.policy import default
from random import choices
import mongoengine as me
import datetime

SEMESTER_TYPE = [("midterm", "Midterm"), ("final", "Final")]


class Grade(me.Document):
    meta = {"collection": "grades"}

    type = me.StringField(choices=SEMESTER_TYPE)
    class_ = me.ReferenceField("Class", dbref=True, required=True)
    student_ids = me.ListField()
    student_grades = me.ListField()

    teacher = me.ReferenceField("User", dbref=True, required=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )


class StudentGrade(me.Document):
    meta = {"collection": "student_grades"}

    result = me.StringField(default="-")
    grade = me.ReferenceField("Grade", dbref=True, required=True)
    student = me.ReferenceField("User", dbref=True, required=True)
