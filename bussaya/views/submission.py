from flask import Blueprint, render_template, redirect, url_for, send_file
from flask_login import login_required, current_user
from .. import forms
from .. import models
import mongoengine as me

import datetime

module = Blueprint("submission", __name__, url_prefix="/")


@module.route("/<class_id>/submissions/add", methods=["GET", "POST"])
@login_required
def add(class_id):
    form = forms.submissions.SubmissionForm()
    class_ = models.Class.objects.get(id=class_id)
    if not form.validate_on_submit():
        return render_template(
            "/submissions/add-edit.html",
            form=form,
            class_=class_,
        )

    submissions = models.Submission()
    form.populate_obj(submissions)
    submissions.class_ = class_
    submissions.owner = current_user._get_current_object()
    submissions.save()

    return redirect(
        url_for("admin.classes.view", class_id=class_id, submissions=submissions)
    )


@module.route(
    "/admin/classes/<class_id>/submissions/<submission_id>", methods=["GET", "POST"]
)
@login_required
def view(submission_id, class_id):
    form = forms.submissions.SubmissionForm()
    submission = models.Submission.objects.get(id=submission_id)
    class_ = models.Class.objects.get(id=class_id)
    return render_template(
        "/submissions/view.html", submission=submission, class_=class_
    )


@module.route("<class_id>/submissions/<submission_id>/edit", methods=["GET", "POST"])
@login_required
def edit(submission_id, class_id):
    class_ = models.Class.objects.get(id=class_id)
    submission = models.Submission.objects.get(id=submission_id)
    form = forms.submissions.SubmissionForm(obj=submission)
    if not form.validate_on_submit():
        return render_template(
            "/submissions/add-edit.html",
            form=form,
            class_=class_,
            submission=submission,
        )

    form.populate_obj(submission)
    submission.save()

    submissions = models.Submission()
    return redirect(
        url_for("admin.classes.view", class_id=class_id, submissions=submissions)
    )


@module.route("/<class_id>/submissions/<submission_id>/delete", methods=["GET", "POST"])
@login_required
def delete(submission_id, class_id):
    submission = models.Submission.objects.get(id=submission_id)
    submission.delete()
    return redirect(
        url_for("admin.classes.view", submission=submission, class_id=class_id)
    )
