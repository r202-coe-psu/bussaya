from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from .. import forms
from .. import models
import mongoengine as me

import datetime
import socket

module = Blueprint("submissions", __name__, url_prefix="/submissions")


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
    "/classes/<class_id>/submissions/<submission_id>", methods=["GET", "POST"]
)
@login_required
def view(submission_id, class_id):
    form = forms.submissions.SubmissionForm()
    submission = models.Submission.objects.get(id=submission_id)
    class_ = models.Class.objects.get(id=class_id)
    student_works = models.StudentWork.objects.all().filter(
        class_=class_, submission=submission
    )

    return render_template(
        "/submissions/view.html",
        submission=submission,
        class_=class_,
        student_works=student_works,
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
    print(submission_id)
    submission = models.Submission.objects.get(id=submission_id)
    submission.delete()
    return redirect(
        url_for("admin.classes.view", submission=submission, class_id=class_id)
    )


@module.route(
    "/classes/<class_id>/submission/form/<submission_id>/",
    methods=["GET", "POST"],
)
@login_required
def upload(submission_id, class_id):

    form = forms.submissions.StudentWorkForm()
    submission = models.Submission.objects.get(id=submission_id)
    class_ = models.Class.objects.get(id=class_id)

    if not form.validate_on_submit():
        return render_template(
            "/submissions/upload.html",
            form=form,
            submission=submission,
            class_=class_,
        )

    student_submission = models.StudentWork()

    student_submission.owner = current_user._get_current_object()
    student_submission.ip_address = request.remote_addr

    student_submission.class_ = models.Class.objects.get(id=class_id)
    student_submission.submission = models.Submission.objects.get(id=submission_id)

    form.populate_obj(student_submission)
    if form.uploaded_file.data:
        if not student_submission.file:
            student_submission.file.put(
                form.uploaded_file.data,
                filename=form.uploaded_file.data.filename,
                content_type="application/pdf",
            )
        else:
            student_submission.file.replace(
                form.uploaded_file.data,
                filename=form.uploaded_file.data.filename,
                content_type="application/pdf",
            )

    student_submission.save()

    return redirect(url_for("classes.view", submission=submission, class_id=class_id))


@module.route(
    "/<student_work_id>/<filename>",
)
@login_required
def download(student_work_id, filename):

    student_work = models.StudentWork.objects.get(id=student_work_id)

    if (
        not student_work
        or not student_work.file
        or student_work.file.filename != filename
    ):
        return abort(403)

    response = send_file(
        student_work.file,
        attachment_filename=student_work.file.filename,
        mimetype=student_work.file.content_type,
    )

    return response
