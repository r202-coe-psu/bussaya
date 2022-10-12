from typing import final
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    Response,
    request,
)
from flask_login import login_required, current_user

from bussaya import models
from .. import forms

import datetime


module = Blueprint("final_reports", __name__, url_prefix="/final_reports")


@module.route("/")
def index():
    # need implement
    return redirect(url_for("classes.index"))


def get_resource(data, type, project_id):
    resource = models.ProjectResource()
    resource.type = type
    resource.link = url_for(
        "projects.download",
        project_id=project_id,
        resource_id=resource.id,
        filename=data.filename,
    )
    resource.data.put(data, filename=data.filename, content_type=data.content_type)

    return resource


@module.route("/<final_submission_id>/upload", methods=["GET", "POST"])
@login_required
def upload(final_submission_id):
    final_submission = models.FinalSubmission.objects.get(id=final_submission_id)
    class_ = final_submission.class_
    project = current_user._get_current_object().get_project()

    form = forms.submissions.FinalReportForm()
    if not form.validate_on_submit():
        return render_template(
            "/final_reports/upload.html",
            form=form,
            final_submission=final_submission,
            class_=class_,
        )

    final_report = models.FinalReport.objects(final_submission=final_submission).first()
    if not final_report:
        final_report = models.FinalReport()

    final_report.final_submission = final_submission
    final_report.project = project
    final_report.class_ = class_
    final_report.owner = current_user._get_current_object()
    final_report.ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )
    final_report.save()

    files = [
        form.report.data,
        form.presentation.data,
        form.similarity.data,
        form.poster.data,
        form.other.data,
    ]
    types = ["report", "presentation", "similarity", "poster", "other"]

    for f, t in zip(files, types):
        if not f:
            continue
        resource = get_resource(f, t, project.id)
        project.resources.append(resource)

    files = [form.video.data, form.git.data]
    types = ["video", "git"]
    for f, t in zip(files, types):
        if not f:
            continue
        resource = models.ProjectResource(type=t, link=f)
        project.resources.append(resource)
    project.save()

    return redirect(url_for("classes.index", class_id=class_.id))
