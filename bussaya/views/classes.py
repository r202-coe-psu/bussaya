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
