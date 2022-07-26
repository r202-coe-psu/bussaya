from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user

from bussaya.models.submissions import MeetingReport
from .. import forms
from .. import models
import mongoengine as me

from bussaya import acl

import datetime
import socket

module = Blueprint("meetings", __name__, url_prefix="/meetings")


@module.route("/<meeting_id>/")
@login_required
def view(meeting_id):
    if current_user.has_roles("admin"):
        return view_admin(meeting_id)
    else:
        return view_lecturer(meeting_id)


@module.route("/<meeting_id>/view/admin", methods=["GET", "POST"])
@login_required
def view_admin(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    meeting_reports = models.MeetingReport.objects.all().filter(
        class_=meeting.class_, meeting=meeting
    )

    form = forms.meetings.DisapproveForm()

    if request.method == "POST":
        meeting_report = models.MeetingReport.objects.get(
            id=request.form.get("meeting_report_id")
        )
        meeting_report.remark = form.remark.data
        meeting_report.save()

        approval(
            meeting_id=meeting.id,
            meeting_report_id=meeting_report.id,
            action="disapproved",
        )

    return render_template(
        "/admin/meetings/view.html",
        meeting=meeting,
        class_=meeting.class_,
        meeting_reports=meeting_reports,
        form=form,
    )


@module.route("/<meeting_id>/view", methods=["GET", "POST"])
@login_required
def view_lecturer(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    meeting_reports = models.MeetingReport.objects.all().filter(
        class_=meeting.class_, meeting=meeting
    )

    form = forms.meetings.DisapproveForm()

    if request.method == "POST":
        meeting_report = models.MeetingReport.objects.get(
            id=request.form.get("meeting_report_id")
        )
        meeting_report.remark = form.remark.data
        meeting_report.save()

        approval(
            meeting_id=meeting.id,
            meeting_report_id=meeting_report.id,
            action="disapproved",
        )

    return render_template(
        "/meetings/view.html",
        meeting=meeting,
        class_=meeting.class_,
        meeting_reports=meeting_reports,
        form=form,
    )


@module.route(
    "/<meeting_id>/students/<meeting_report_id>/approval/<action>",
    methods=["GET", "POST"],
)
@login_required
def approval(meeting_id, meeting_report_id, action):

    meeting_report = models.MeetingReport.objects.get(id=meeting_report_id)
    meeting_report.status = action
    if action == "approved":
        meeting_report.remark = None

    meeting_report.save()

    return redirect(url_for("meetings.view", meeting_id=meeting_id))


@module.route(
    "/create/<class_id>/<name>/<grade>/<start>/<end>", methods=["GET", "POST"]
)
@acl.roles_required("admin")
def create(class_id, name, grade, start, end):
    class_ = models.Class.objects.get(id=class_id)

    meeting = models.Meeting()
    meeting.name = name
    meeting.grade = grade
    meeting.started_date = start
    meeting.ended_date = end
    meeting.class_ = class_
    meeting.owner = current_user._get_current_object()
    meeting.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<meeting_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def edit(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = meeting.class_

    form = forms.meetings.MeetingForm()
    if request.method == "GET":
        form = forms.meetings.MeetingForm(obj=meeting)

    if not form.validate_on_submit():
        return render_template("/admin/meetings/edit.html", class_=class_, form=form)

    form.populate_obj(meeting)
    meeting.save()
    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<meeting_id>/delete", methods=["GET", "POST"])
@acl.roles_required("admin")
def delete(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    student_meeting_report = models.MeetingReport.objects(meeting=meeting)

    student_meeting_report.delete()
    meeting.delete()

    class_ = meeting.class_
    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<meeting_id>/upload", methods=["GET", "POST"])
@login_required
def report(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = meeting.class_

    form = forms.meetings.MeetingReportForm()

    if meeting.get_status() == "closed":
        return redirect(url_for("classes.view", class_id=class_.id))

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report-edit.html", meeting=meeting, class_=class_, form=form
        )

    meeting_report = models.MeetingReport()
    meeting_report.owner = current_user._get_current_object()
    meeting_report.ip_address = request.remote_addr

    meeting_report.class_ = models.Class.objects.get(id=class_.id)
    meeting_report.meeting = models.Meeting.objects.get(id=meeting_id)

    form.populate_obj(meeting_report)
    meeting_report.save()

    return redirect(url_for("classes.view", class_id=class_.id))


@module.route("/report/<meeting_report_id>/edit", methods=["GET", "POST"])
@login_required
def edit_report(meeting_report_id):

    meeting_report = models.MeetingReport.objects.get(id=meeting_report_id)
    meeting = meeting_report.meeting
    class_ = meeting_report.class_

    if meeting.get_status() == "closed":
        return redirect(url_for("classes.view", class_id=class_.id))

    form = forms.meetings.MeetingReportForm(obj=meeting_report)

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report-edit.html",
            meeting=meeting,
            class_=class_,
            form=form,
            meeting_report=meeting_report,
        )

    meeting_report.owner = current_user._get_current_object()
    meeting_report.ip_address = request.remote_addr

    form.populate_obj(meeting_report)
    meeting_report.save()

    return redirect(url_for("classes.view", class_id=class_.id))
