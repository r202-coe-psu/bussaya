from flask import Blueprint, render_template, url_for, redirect
from flask_login import current_user, login_required
import mongoengine as me
from datetime import datetime
from bussaya import acl

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

    meeting_reports = models.MeetingReport.objects(
        class_=class_, project__in=projects
    ).order_by("-updated_date")
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

    return render_template(
        "/classes/view-lecturer.html",
        class_=class_,
        class_id=class_id,
        projects=projects,
        meeting_reports=meeting_reports,
        progress_reports=progress_reports,
        advisee_projects=advisee_projects,
        committee_projects=committee_projects,
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


@module.route("/<class_id>/students")
@login_required
def view_students(class_id):
    class_ = models.Class.objects.get(id=class_id)
    # projects = models.Project.objects(
    #     me.Or(
    #         creators=current_user._get_current_object(),
    #         students=current_user._get_current_object(),
    #     )
    # )

    students = []
    for id in class_.student_ids:
        student = models.User.objects(username=id).first()
        if not student or "student" not in student.roles:
            continue
        students.append(student)

    return render_template("/classes/students.html", class_=class_, students=students)
