from flask import Blueprint, render_template, url_for, redirect
from flask_login import current_user, login_required

from .. import models
from datetime import datetime

from bussaya import acl

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
    if "CoE-lecturer" in current_user.roles:
        return view_lecturer(class_id)
    elif "student" in current_user.roles:
        return view_student(class_id)


@module.route("/lecturer/<class_id>/view")
@acl.roles_required("CoE-lecturer")
def view_lecturer(class_id):
    class_ = models.Class.objects.get(id=class_id)
    projects = models.Project.objects(class_=class_)
    submissions = models.Submission.objects(class_=class_)
    meetings = models.Meeting.objects(class_=class_)

    return render_template(
        "/classes/view-lecturer.html",
        class_=class_,
        class_id=class_id,
        projects=projects,
        submissions=submissions,
        meetings=meetings,
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

    return render_template(
        "/classes/view-student.html",
        user=user,
        class_=class_,
        submissions=submissions,
        meetings=meetings,
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


@module.route("/<class_id>/student_ids")
@login_required
def view_students(class_id):
    class_ = models.Class.objects.get(id=class_id)

    students = []
    for id in class_.student_ids:
        student = models.User.objects(username=id).first()
        if not student or "student" not in student.roles:
            continue
        students.append(student)

    return render_template("/classes/students.html", class_=class_, students=students)
