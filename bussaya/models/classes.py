import mongoengine as me
import datetime

from . import users
from . import projects

TYPE_CHOICE = [
    ("preproject", "Preproject"),
    ("project", "Project"),
    ("cooperative", "Cooperative Education"),
    ("precooperative", "Pre-cooperative Education"),
]


class Class(me.Document):
    meta = {"collection": "classes"}

    name = me.StringField(required=True, max_length=255)
    description = me.StringField()
    code = me.StringField(max_length=100)
    student_ids = me.ListField(me.StringField())

    tags = me.ListField(me.StringField(required=True))
    type = me.StringField(choices=TYPE_CHOICE)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateField(required=True, default=datetime.datetime.today)
    ended_date = me.DateField(required=True, default=datetime.datetime.today)

    owner = me.ReferenceField("User", dbref=True, required=True)

    def get_students(self):
        return users.User.objects(username__in=self.student_ids).order_by("username")

    def get_projects_by_advisors(self, *args):
        return projects.Project.objects(advisors__in=args)

    def get_projects(self):
        students = self.get_students()
        return projects.Project.objects(
            me.Q(creator__in=students) | me.Q(students__in=students)
        ).order_by("name")

    def is_available_project(self, project):
        for student in project.students:
            if str(student.username) not in self.student_ids:
                return False
        return True

    def get_advisees_by_advisors(self, *args):
        students = self.get_students()
        # adv_projects = projects.Project.objects(advisor__in=args, students__in=students)
        adv_projects = projects.Project.objects(advisors=args, students__in=students)
        return [s for project in adv_projects for s in project.students]

    def is_in_time(self):
        return self.started_date <= datetime.datetime.now().date() <= self.ended_date

    def count_grade(self, round_grade):
        student_ids = self.student_ids

        grades = {
            "A": [0, []],
            "B+": [0, []],
            "B": [0, []],
            "C+": [0, []],
            "C": [0, []],
            "D+": [0, []],
            "D": [0, []],
            "E": [0, []],
            "I": [0, []],
            "W": [0, []],
        }

        for i in student_ids:
            user = users.User.objects.get(username=i)

            grade, caused = users.User.get_actual_grade(
                self=user, round_grade=round_grade
            )

            if grade in grades:
                grades[grade][0] += 1
                grades[grade][1].append(user)
            else:
                grades[grade] = [1, [user]]

        return grades
