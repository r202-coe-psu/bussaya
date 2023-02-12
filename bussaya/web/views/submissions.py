from os import abort
from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user

from bussaya import models

from .. import forms
from .. import acl

import mongoengine as me

import datetime
import socket

module = Blueprint("submissions", __name__, url_prefix="/submissions")


@module.route("/create", methods=["GET", "POST"])
@login_required
def create():
    class_id = request.args.get("class_id", None)
    if not class_id:
        return redirect(url_for("dashboard.index"))

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


@module.route("/<submission_id>/lecturer-view")
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


@module.route("/<submission_id>/admin-view")
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
    progress_reports = models.ProgressReport.objects(submission=submission).delete()

    class_ = submission.class_
    submission.delete()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route(
    "/<submission_id>/upload",
    methods=["GET", "POST"],
)
@login_required
def upload(submission_id):
    user = current_user._get_current_object()
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

    progress_report = models.ProgressReport.objects(
        submission=submission, owner=user
    ).first()
    if not progress_report:
        progress_report = models.ProgressReport()
        progress_report.submission = models.Submission.objects.get(id=submission_id)
        progress_report.class_ = submission.class_

    progress_report.updated_date = datetime.datetime.now()
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


@module.route(
    "/<submission_id>/reports/admin-force-create",
    methods=["GET", "POST"],
)
# @module.route(
#     "/<submission_id>/reports/<meeting_report_id>/admin-force-edit",
#     methods=["GET", "POST"],
# )
@acl.roles_required("admin")
def force_report(submission_id):
    user = current_user._get_current_object()
    submission = models.Submission.objects.get(id=submission_id)
    class_ = submission.class_

    projects = class_.get_projects()
    students = class_.get_students()

    form = forms.submissions.AdminProgressReportForm()
    form.project.queryset = projects
    form.student.choices = [
        (
            str(student.id),
            f"{student.username} ({student.first_name} {student.last_name})",
        )
        for student in students
    ]

    if not form.validate_on_submit() or not form.uploaded_file.data:
        return render_template(
            "/admin/submissions/upload.html",
            form=form,
            submission=submission,
            class_=class_,
            projects=projects,
        )

    progress_report = models.ProgressReport.objects(
        submission=submission, owner=user
    ).first()
    if not progress_report:
        progress_report = models.ProgressReport()
        progress_report.submission = models.Submission.objects.get(id=submission_id)
        progress_report.class_ = submission.class_

    progress_report.updated_date = form.uploaded_date.data
    progress_report.owner = models.User.objects.get(id=form.student.data)
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

    return redirect(url_for("submissions.view", submission_id=submission.id))


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
        download_name=progress_report.file.filename,
        mimetype=progress_report.file.content_type,
    )

    return response


@module.route(
    "/<class_id>/upload_final_report",
)
@login_required
def upload_final_report(class_id):
    class_ = models.Class.objects.get(id=class_id)
    form = forms.submissions.FinalReport()

    if not form.validate_on_submit():
        return render_template(
            "/submissions/upload-final-report.html", class_=class_, form=form
        )

    return redirect(url_for("classes.view", class_id=class_.id))
