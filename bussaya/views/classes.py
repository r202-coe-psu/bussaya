from flask import Blueprint, render_template, url_for, redirect, request
from flask_login import current_user, login_required
import mongoengine as me
from datetime import datetime
from bussaya import acl, forms

from .. import models


module = Blueprint(
    "classes",
    __name__,
    url_prefix="/classes",
)


@module.route("")
@acl.roles_required("lecturer")
def index():
    classes = models.Class.objects().order_by("-id")
    return render_template("/classes/index.html", classes=classes)


@module.route("/<class_id>")
@login_required
def view(class_id):
    # if "admin" in current_user.roles:
    #     return redirect(url_for("admin.classes.view", class_id=class_id))
    if "CoE-lecturer" in current_user.roles or "lecturer" in current_user.roles:
        return view_lecturer(class_id)
    if "student" in current_user.roles:
        return view_student(class_id)

    return redirect(url_for("dashboard.index"))


@module.route("/lecturer/<class_id>/view")
@acl.roles_required("CoE-lecturer")
def view_lecturer(class_id):
    class_ = models.Class.objects.get(id=class_id)
    students = models.User.objects(username__in=class_.student_ids)
    projects = models.Project.objects(
        advisor=current_user._get_current_object(), students__in=students
    )
    submissions = models.Submission.objects(class_=class_)
    meetings = models.Meeting.objects(class_=class_)

    # meeting_reports = models.MeetingReport.objects(
    #     class_=class_, project__in=projects
    # ).order_by("-meeting_date")
    progress_reports = models.ProgressReport.objects(
        class_=class_, project__in=projects
    )

    student_ids = class_.student_ids

    students = models.User.objects(username__in=student_ids)

    advisee_projects = models.Project.objects(
        advisor=current_user._get_current_object(), students__in=students
    )
    committee_projects = models.Project.objects(
        committees=current_user._get_current_object(), students__in=students
    )

    current_advisees = []
    for project in advisee_projects:
        current_advisees.extend(project.students)

    return render_template(
        "/classes/view-lecturer.html",
        class_=class_,
        class_id=class_id,
        projects=projects,
        # meeting_reports=meeting_reports,
        progress_reports=progress_reports,
        advisee_projects=advisee_projects,
        committee_projects=committee_projects,
        current_advisees=current_advisees,
    )


@module.route("/student/<class_id>/view")
@login_required
def view_student(class_id):
    class_ = models.Class.objects.get(id=class_id)
    submissions = models.Submission.objects.all().filter(
        class_=class_,
    )
    meetings = models.Meeting.objects.all().filter(class_=class_)
    user = current_user._get_current_object()

    round_grades = models.RoundGrade.objects(class_=class_)

    grade_released = False
    for grade in round_grades:
        if grade.release_status == "released":
            grade_released = True

    return render_template(
        "/classes/view-student.html",
        user=user,
        class_=class_,
        submissions=submissions,
        meetings=meetings,
        grade_released=grade_released,
    )


def get_student_name(student_id):
    student = models.User.objects(username=student_id).first()
    if not student:
        return ""

    return f"{student.first_name} {student.last_name}"


def get_student_group(student_id, class_id):
    student = models.User.objects(username=student_id).first()
    class_ = models.Class.objects.get(id=class_id)

    groups = models.Group.objects.all().filter(class_=class_)
    for group in groups:
        if student in group.students:
            return group.name

    return ""


@module.route("/<class_id>/students/<user_id>/meeting_reports")
@acl.roles_required("lecturer", "admin")
def list_report_by_user(class_id, user_id):

    round = request.args.get("round", None)
    class_ = models.Class.objects.get(id=class_id)

    meetings = []
    if round:
        meetings = models.Meeting.objects(class_=class_, round=round)
    else:
        meetings = models.Meeting.objects(class_=class_)

    user = models.User.objects.get(id=user_id)
    meeting_reports = models.MeetingReport.objects(meeting__in=meetings, owner=user)

    form = forms.meetings.DisapproveForm()

    return render_template(
        "/classes/list-report-by-user.html",
        class_=class_,
        user=user,
        meeting_reports=meeting_reports,
        form=form,
    )


def get_student_by_id(student_id, students):
    for s in students:
        if s.username == student_id:
            return s

    return None


@module.route("/<class_id>/students")
@acl.roles_required("admin")
def view_students(class_id):
    class_ = models.Class.objects.get(id=class_id)
    students = models.User.objects(username__in=class_.student_ids).order_by(
        "-username"
    )

    return render_template(
        "/classes/students.html",
        class_=class_,
        students=students,
        get_student_by_id=get_student_by_id,
    )
