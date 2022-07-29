from os import abort
from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from .. import forms
from .. import models

from bussaya import acl

import mongoengine as me

import datetime
import socket

module = Blueprint("submissions", __name__, url_prefix="/submissions")


@module.route("/<class_id>/submission/create", methods=["GET", "POST"])
@login_required
def create(class_id):
    form = forms.submissions.SubmissionForm()
    class_ = models.Class.objects.get(id=class_id)
    if not form.validate_on_submit():
        return render_template(
            "/admin/submissions/create-edit.html",
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


@module.route("/<submission_id>")
@login_required
def view(submission_id):
    if current_user.has_roles("admin"):
        return view_admin(submission_id)
    else:
        return view_lecturer(submission_id)


@module.route("/<submission_id>/view")
@login_required
def view_lecturer(submission_id):
    submission = models.Submission.objects.get(id=submission_id)
    class_ = submission.class_
    progress_reports = models.ProgressReport.objects.all().filter(
        class_=class_, submission=submission
    )
    return render_template(
        "/submissions/view.html",
        submission=submission,
        class_=class_,
        progress_reports=progress_reports,
    )


@module.route("/<submission_id>/admin/view")
@acl.roles_required("admin")
def view_admin(submission_id):
    submission = models.Submission.objects.get(id=submission_id)
    class_ = submission.class_
    progress_reports = models.ProgressReport.objects.all().filter(
        class_=class_, submission=submission
    )
    return render_template(
        "/admin/submissions/view.html",
        submission=submission,
        class_=class_,
        progress_reports=progress_reports,
    )


@module.route("/<submission_id>/edit", methods=["GET", "POST"])
@login_required
def edit(submission_id):
    submission = models.Submission.objects.get(id=submission_id)
    class_ = submission.class_

    form = forms.submissions.SubmissionForm(obj=submission)
    if not form.validate_on_submit():
        return render_template(
            "/admin/submissions/create-edit.html",
            form=form,
            class_=class_,
            submission=submission,
        )

    form.populate_obj(submission)
    submission.save()

    submissions = models.Submission()
    return redirect(
        url_for("admin.classes.view", class_id=class_.id, submissions=submissions)
    )


@module.route("/<submission_id>/delete", methods=["GET", "POST"])
@login_required
def delete(submission_id):
    submission = models.Submission.objects.get(id=submission_id)
    submission.delete()

    progress_reports = models.ProgressReport.objects(submission=submission)
    [progress_report.delete for progress_report in progress_reports]

    return redirect(
        url_for(
            "admin.classes.view", submission=submission, class_id=submission.class_.id
        )
    )


@module.route(
    "/<submission_id>/upload",
    methods=["GET", "POST"],
)
@login_required
def upload(submission_id):
    submission = models.Submission.objects.get(id=submission_id)
    class_ = submission.class_
    if submission.get_status() == "closed":
        return redirect(url_for("classes.view", class_id=class_.id))

    projects = models.Project.objects(
        me.Q(creator=current_user._get_current_object())
        | me.Q(students=current_user._get_current_object())
    )

    form = forms.submissions.ProgressReportForm()
    form.project.queryset = projects

    if not form.validate_on_submit() or not form.uploaded_file.data:
        return render_template(
            "/submissions/upload.html",
            form=form,
            submission=submission,
            class_=class_,
            projects=projects,
        )

    progress_report = models.ProgressReport.objects(submission=submission).first()
    if not progress_report:
        progress_report = models.ProgressReport()
        progress_report.submission = models.Submission.objects.get(id=submission_id)
        progress_report.class_ = submission.class_

    progress_report.owner = current_user._get_current_object()
    progress_report.ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )

    form.populate_obj(progress_report)
    if not progress_report.file:
        progress_report.file.put(
            form.uploaded_file.data,
            filename=form.uploaded_file.data.filename,
            content_type=form.uploaded_file.data.content_type,
        )
    else:
        progress_report.file.replace(
            form.uploaded_file.data,
            filename=form.uploaded_file.data.filename,
            content_type=form.uploaded_file.data.content_type,
        )

    progress_report.save()

    return redirect(url_for("classes.view", class_id=class_.id))


# @module.route(
#     "/<progress_report_id>/form/edit",
#     methods=["GET", "POST"],
# )
# @login_required
# def edit_progress_report(progress_report_id):

#     progress_report = models.ProgressReport.objects.get(id=progress_report_id)
#     submission = progress_report.submission
#     class_ = progress_report.class_

#     form = forms.submissions.StudentWorkForm(obj=progress_report)

#     if submission.get_status() == "closed":
#         return redirect(url_for("classes.view", class_id=class_.id))

#     if request.method == "GET":
#         return render_template(
#             "/submissions/upload-edit.html",
#             form=form,
#             class_=class_,
#             submission=submission,
#             progress_report=progress_report,
#         )

#     print(progress_report.updated_date)
#     progress_report.updated_date = datetime.datetime.now()

#     progress_report.owner = current_user._get_current_object()
#     progress_report.ip_address = request.remote_addr

#     progress_report.submission = submission
#     progress_report.class_ = class_

#     form.populate_obj(progress_report)
#     if form.uploaded_file.data:
#         if not progress_report.file:
#             progress_report.file.put(
#                 form.uploaded_file.data,
#                 filename=form.uploaded_file.data.filename,
#                 content_type="application/pdf",
#             )
#         else:
#             progress_report.file.replace(
#                 form.uploaded_file.data,
#                 filename=form.uploaded_file.data.filename,
#                 content_type="application/pdf",
#             )

#     progress_report.save()

#     return redirect(url_for("classes.view", class_id=class_.id))


@module.route(
    "/<progress_report_id>/<filename>",
)
@login_required
def download(progress_report_id, filename):

    progress_report = models.ProgressReport.objects.get(id=progress_report_id)

    if (
        not progress_report
        or not progress_report.file
        or progress_report.file.filename != filename
    ):
        return abort(403)

    response = send_file(
        progress_report.file,
        attachment_filename=progress_report.file.filename,
        mimetype=progress_report.file.content_type,
    )

    return response
