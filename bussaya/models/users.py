import datetime
import mongoengine as me

from flask import url_for
from flask_login import UserMixin

from bussaya import models


class User(me.Document, UserMixin):
    username = me.StringField(required=True, unique=True, max_length=200)

    title = me.StringField(max_length=50)
    email = me.StringField(required=True, unique=True, max_length=200)
    first_name = me.StringField(required=True, max_length=200)
    last_name = me.StringField(required=True, max_length=200)

    title_th = me.StringField(max_length=50)
    first_name_th = me.StringField(max_length=200)
    last_name_th = me.StringField(max_length=200)

    biography = me.StringField()

    picture = me.ImageField(thumbnail_size=(800, 600, True))

    status = me.StringField(required=True, default="disactive")
    roles = me.ListField(me.StringField(), default=["user"], max_length=200)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    last_login_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    resources = me.DictField()

    meta = {"collection": "users", "strict": False}

    def get_fullname(self):
        return self.first_name + " " + self.last_name

    def has_roles(self, *roles):
        for role in roles:
            if role in self.roles:
                return True
        return False

    def get_picture(self):
        if self.picture:
            return url_for(
                "accounts.picture", user_id=self.id, filename=self.picture.filename
            )
        if "google" in self.resources:
            return self.resources["google"].get("picture", "")
        return url_for("static", filename="images/user.png")

    def get_project(self):
        project = models.Project.objects(students=self).order_by("-id").first()
        return project

    def get_report(self, class_id):
        class_ = models.Class.objects.get(id=class_id)
        progress_reports = models.ProgressReport.objects(class_=class_, owner=self)

        for progress_report in progress_reports:
            return progress_report
        return False

    def get_presentation(self, class_id):
        class_ = models.Class.objects.get(id=class_id)
        progress_report = models.ProgressReport.objects(
            class_=class_, owner=self
        ).first()

        return progress_report

    def get_meeting_reports(self, class_, round=None):
        from . import submissions

        meetings = submissions.Meeting.objects(class_=class_)
        if round:
            meetings = meetings.filter(round=round)

        meeting_reports = submissions.MeetingReport.objects(
            meeting__in=meetings, owner=self
        )
        return meeting_reports

    def get_advisee_projects(self):
        projects = models.Project.objects(advisor=self).order_by("-id")
        return projects

    def get_group(self, class_):
        for group in models.Group.objects(class_=class_):
            if self in group.committees:
                return group

    def get_total_student_grades(self, round_grade):
        student_grades = models.StudentGrade.objects(
            student=self, class_=round_grade.class_, round_grade=round_grade
        )
        return student_grades

    def get_total_lecturer_grades(self, round_grade):
        student_grades = models.StudentGrade.objects(
            lecturer=self, class_=round_grade.class_, round_grade=round_grade
        )
        return student_grades

    def get_average_grade(self, round_grade):
        student_grades = models.StudentGrade.objects(
            student=self, class_=round_grade.class_, round_grade=round_grade
        )

        total_student_grade = []
        for student_grade in student_grades:
            if student_grade.result != "-":
                total_student_grade.append(student_grade)

        if len(total_student_grade) < 2:
            return "Incomplete"

        average_point = 0
        committees_grade_point = 0

        project = self.get_project()

        if len(project.committees) > 1:
            advisor_grade_ratio = 0.5
            committee_grade_ratio = 0.5
        else:
            advisor_grade_ratio = 0.6
            committee_grade_ratio = 0.4

        for round_grade in total_student_grade:
            grade_point = round_grade.get_grade_point()

            if round_grade.lecturer in project.committees:
                committees_grade_point += grade_point

            else:
                average_point += advisor_grade_ratio * grade_point

        average_point += committee_grade_ratio * committees_grade_point

        if average_point > 3.75:
            average_grade = "A"
        elif average_point >= 3.25:
            average_grade = "B+"
        elif average_point >= 2.75:
            average_grade = "B"
        elif average_point >= 2.25:
            average_grade = "C+"
        elif average_point >= 1.75:
            average_grade = "C"
        elif average_point >= 1.25:
            average_grade = "D+"
        elif average_point >= 0.75:
            average_grade = "D"
        elif average_point < 0.5:
            average_grade = "E"

        return average_grade

    def get_permission_to_upload(self, submission):
        meeting_reports = models.MeetingReport.objects(
            class_=submission.class_, owner=self
        )
        count_report = 0
        for report in meeting_reports:
            if submission.round == report.meeting.round:
                count_report += 1

        if count_report > 2:
            return True
        return False
