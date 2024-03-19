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

    title_th = me.StringField(max_length=50, default="")
    first_name_th = me.StringField(max_length=200, default="")
    last_name_th = me.StringField(max_length=200, default="")

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

    @property
    def fullname(self):
        return self.get_fullname()

    def get_fullname(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

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
        project = (
            models.Project.objects(students=self, status="active")
            .order_by("-id")
            .first()
        )
        return project

    def get_report(self, class_, round):
        submission = models.Submission.objects(
            type="report", class_=class_, round=round
        ).first()
        progress_report = models.ProgressReport.objects(
            owner=self, submission=submission
        ).first()

        return progress_report

    def get_presentation(self, class_, round):

        submission = models.Submission.objects(
            type="presentation", class_=class_, round=round
        ).first()

        progress_report = models.ProgressReport.objects(
            owner=self, submission=submission
        ).first()

        return progress_report

    def get_meeting_reports(self, class_, round=None, approval_status=None):
        meetings = models.Meeting.objects(class_=class_)
        if round:
            meetings = meetings.filter(round=round)

        meeting_reports = models.MeetingReport.objects(meeting__in=meetings, owner=self)
        if approval_status:
            meeting_reports = meeting_reports.filter(status=approval_status)

        return meeting_reports

    def get_advisee_projects(self):
        projects = models.Project.objects(
            advisors=self, class___ne=None, status="active"
        ).order_by("-id")
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
            grader__lecturer=self, class_=round_grade.class_, round_grade=round_grade
        )
        return student_grades

    def get_permission_to_upload(self, submission):
        if submission.class_ and submission.class_.type == "cooperative":
            return True

        meetings = models.Meeting.objects(
            class_=submission.class_,
            round=submission.round,
        )
        report_count = models.MeetingReport.objects(
            class_=submission.class_,
            owner=self,
            status__in=["approved", "wait", None],
            meeting__in=meetings,
        ).count()

        if report_count > 2:
            return True

        return False

    def get_grade_to_point(self, grade):
        point = 0
        if grade == "A":
            point = 4
        elif grade == "B+":
            point = 3.5
        elif grade == "B":
            point = 3
        elif grade == "C+":
            point = 2.5
        elif grade == "C":
            point = 2
        elif grade == "D+":
            point = 1.5
        elif grade == "D":
            point = 1
        elif grade == "E":
            point = 0.5

        return point

    def get_point_to_grade(self, point):
        grade = "-"

        if point >= 3.75:
            grade = "A"
        elif point >= 3.25:
            grade = "B+"
        elif point >= 2.75:
            grade = "B"
        elif point >= 2.25:
            grade = "C+"
        elif point >= 1.75:
            grade = "C"
        elif point >= 1.25:
            grade = "D+"
        elif point >= 0.75:
            grade = "D"
        else:
            grade = "E"

        return grade

    def get_average_grade(self, round_grade):
        class_ = round_grade.class_
        student_grades = models.StudentGrade.objects(
            student=self, class_=class_, round_grade=round_grade
        )

        has_advisor = False
        total_student_grade = []
        for student_grade in student_grades:
            if student_grade.result in ["I", "W"]:
                return student_grade.result

            elif student_grade.result != "-":
                total_student_grade.append(student_grade)
                if student_grade.grader.lecturer in student_grade.project.advisors:
                    has_advisor = True

        if not has_advisor:
            return "missing advisor grade"

        if len(total_student_grade) < 2:
            return "uncompleted"

        average_point = 0
        advisor_grade_point = 0
        advisor_count = 0
        committees_grade_point = 0
        committees_count = 0

        project = self.get_project()

        if not project:
            return "project not found"

        if len(project.committees) > 1:
            advisor_grade_ratio = 0.5
            committee_grade_ratio = 0.5
        else:
            advisor_grade_ratio = 0.6
            committee_grade_ratio = 0.4

        for student_grade in total_student_grade:
            grade_point = student_grade.get_grade_point()

            if student_grade.grader.lecturer in project.committees:
                committees_grade_point += grade_point
                committees_count += 1
            elif student_grade.grader.lecturer in project.advisors:
                advisor_grade_point += grade_point
                advisor_count += 1
            elif student_grade.grader.mentor:
                advisor_grade_point += grade_point
                advisor_count += 1

        if advisor_count == 0:
            return "uncompleted"

        if committees_count == 0:
            return "uncompleted"

        average_point = (advisor_grade_point / advisor_count) * advisor_grade_ratio

        average_point += (
            committee_grade_ratio / committees_count
        ) * committees_grade_point

        average_grade = self.get_point_to_grade(average_point)
        return average_grade

    def get_actual_grade(self, round_grade):
        class_ = round_grade.class_

        average_grade = self.get_average_grade(round_grade)
        if average_grade in ["I", "W"]:
            return average_grade, [average_grade]

        final_point = self.get_grade_to_point(average_grade)

        caused = []
        report = self.get_report(class_.id, round_grade.type)
        presentation = self.get_presentation(class_.id, round_grade.type)
        meeting_reports = self.get_meeting_reports(class_, round_grade.type)

        # if grade incomplete
        if len(average_grade) != 1:
            return average_grade, caused

        if presentation:
            delta_time = presentation.submission.ended_date - presentation.updated_date
            if delta_time.days <= -1:
                final_point -= 0.5
                cause = "Presentation Submitted 1 Day Late"
                if delta_time.days <= -2:
                    final_point -= 0.5
                    cause = "Presentation Submitted 2 Day Late"
                caused.append(cause)

        if report:
            delta_time = report.submission.ended_date - report.updated_date
            if delta_time.days <= -1:
                final_point -= 0.5
                cause = "Report Submitted 1 Day Late"
                if delta_time.days <= -2:
                    final_point -= 0.5
                    cause = "Report Submitted 2 Day Late"
                caused.append(cause)

        # if student not sent report -> -0.5 grade
        if not report:
            final_point = 0
            caused.append("Missing Report")

        # if student not sent presentation -> -0.5 grade
        if not presentation:
            final_point -= 0.5
            caused.append("Missing Presentation")

        if round_grade.class_.type != "cooperative":
            if len(meeting_reports) < 4:
                count = 4 - len(meeting_reports)
                if count > 0 or count <= 2:
                    for i in range(count):
                        final_point -= 0.5
                elif count > 2:
                    final_point = 0

                caused.append(f"Missing {count} Meeting report")

        final_grade = self.get_point_to_grade(final_point)

        return final_grade, caused

    def get_complete_grade(self, class_):
        round_grades = models.RoundGrade.objects(class_=class_)

        total_grade = 0
        average_total_grade = "-"

        if len(round_grades) != 2:
            return "uncompleted"

        for round_grade in round_grades:
            actual_grade = self.get_actual_grade(round_grade)

            if actual_grade[0].lower() in ["i", "w"]:
                return actual_grade[0]

            if (
                actual_grade[0].lower() == "uncompleted"
                or round_grade.release_status == "unreleased"
            ):
                return "uncompleted"

            if round_grade.type == "midterm":
                grade_ratio = 0.4
            elif round_grade.type == "final":
                grade_ratio = 0.6

            if actual_grade[0] == "E":
                total_grade = 0
            else:
                total_grade += grade_ratio * self.get_grade_to_point(actual_grade[0])

        if average_total_grade != "uncompleted":
            average_total_grade = self.get_point_to_grade(total_grade)

        return average_total_grade
