from flask import Blueprint, render_template, url_for, redirect
from flask_login import current_user, login_required

from .. import models
from datetime import datetime

module = Blueprint(
    "classes",
    __name__,
    url_prefix="/classes",
)


@module.route("/<class_id>")
@login_required
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    submissions = models.Submission.objects.all().filter(
        class_=class_,
    )
    user = current_user._get_current_object()

    return render_template(
        "/classes/view.html", user=user, class_=class_, submissions=submissions
    )


def get_student_name(student_id):
    student = models.User.objects.get(username=student_id)
    return f"{student.first_name} {student.last_name}"


def get_student_group(student_id, class_id):
    student = models.User.objects.get(username=student_id)
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
    student_ids = class_.student_ids

    return render_template(
        "/classes/students.html",
        class_=class_,
        student_ids=student_ids,
        get_student_name=get_student_name,
        get_student_group=get_student_group,
    )
