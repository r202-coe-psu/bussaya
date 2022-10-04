from os import abort
from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user

from bussaya import acl, forms, models

import mongoengine as me

import datetime
import socket

module = Blueprint("submissions", __name__, url_prefix="/submissions")


@module.route(
    "/<submission_id>/progress_reports/<progress_report_id>/change_reported_date",
    methods=["GET", "POST"],
)
@acl.roles_required("admin")
def change_reported_date(submission_id, progress_report_id):

    submission = models.Submission.objects.get(id=submission_id)
    progress_report = models.ProgressReport.objects.get(id=progress_report_id)
    form = forms.submissions.ProgressReportDateForm(obj=progress_report)

    if not form.validate_on_submit():

        return render_template(
            "/admin/submissions/change_reported_date.html",
            form=form,
            submission=submission,
            class_=submission.class_,
            progress_report=progress_report,
        )

    form.populate_obj(progress_report)
    progress_report.save()

    return redirect(url_for("submissions.view", submission_id=submission_id))
