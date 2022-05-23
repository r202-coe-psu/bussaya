from flask import Blueprint, render_template, redirect, url_for, send_file
from flask_login import login_required, current_user
from .. import forms
from .. import models
import mongoengine as me

import datetime

module = Blueprint("submission", __name__, url_prefix="/")


@module.route("/<class_id>/submission/add", methods=["GET", "POST"])
@login_required
def add(class_id):
    form = forms.submissions.SubmissionForm()
    classes = models.Class.objects.get(id=class_id)
    if not form.validate_on_submit():
        return render_template(
            "/submissions/add.html",
            form=form,
            class_=classes,
        )

    submission = models.Submission()
    form.populate_obj(submission)
    submission.class_ = models.Class.objects.get(id=class_id)
    submission.owner = current_user._get_current_object()
    submission.save()

    return redirect(url_for("admin.classes.view", class_id=class_id))
