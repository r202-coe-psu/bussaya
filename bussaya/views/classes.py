from flask import Blueprint, render_template, url_for, redirect
from flask_login import current_user, login_required

from .. import models
from datetime import datetime

module = Blueprint(
    "classes",
    __name__,
    url_prefix="/classes",
)


def time_in_range(start, end, current):
    return start <= current <= end


@module.route("/")
@login_required
def index():
    classes = models.Class.objects.all()
    now = datetime.now().date()
    available_class = []

    for class_ in classes:
        if time_in_range(class_.started_date, class_.ended_date, now):
            available_class.append(class_)

    return render_template("/classes/index.html", available_class=available_class)


@module.route("/<class_id>")
@login_required
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    submissions = models.Submission.objects.all().filter(
        class_=class_,
    )
    return render_template("/classes/view.html", class_=class_, submissions=submissions)


@module.route("/<class_id>/enroll")
@login_required
def enroll(class_id):
    class_ = models.Class.objects.get(id=class_id)
    student = current_user._get_current_object()

    print(class_.student_ids)
    if student.username not in class_.student_ids:
        class_.student_ids.append(student.username)

    class_.save()
    return redirect(url_for("classes.view", class_id=class_.id))
