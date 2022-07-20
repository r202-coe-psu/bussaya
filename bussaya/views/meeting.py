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


@module.route("/<meeting_id>/view", methods=["GET", "POST"])
@login_required
def view(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    student_works = models.MeetingReport.objects.all().filter(
        class_=meeting.class_, meeting=meeting
    )

    form = forms.meetings.DisapproveForm()

    if request.method == "POST":
        meeting_report = models.MeetingReport.objects.get(
            id=request.form.get("student_work_id")
        )
        meeting_report.remark = form.remark.data
        meeting_report.save()

        approval(
            meeting_id=meeting.id,
            student_work_id=meeting_report.id,
            action="disapproved",
        )

    return render_template(
        "/meetings/view.html",
        meeting=meeting,
        class_=meeting.class_,
        student_works=student_works,
        form=form,
    )


@module.route(
    "/<meeting_id>/students/<student_work_id>/approval/<action>",
    methods=["GET", "POST"],
)
@login_required
def approval(meeting_id, student_work_id, action):

    meeting_report = models.MeetingReport.objects.get(id=student_work_id)
    meeting_report.status = action
    if action == "approved":
        meeting_report.remark = None

    meeting_report.save()

    return redirect(url_for("meetings.view", meeting_id=meeting_id))


@module.route("/<meeting_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
@login_required
def edit(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = meeting.class_

    form = forms.meetings.MeetingForm()
    if request.method == "GET":
        form = forms.meetings.MeetingForm(obj=meeting)

    if not form.validate_on_submit():
        return render_template("/meetings/edit.html", class_=class_, form=form)

    form.populate_obj(meeting)
    meeting.save()
    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<meeting_id>/delete", methods=["GET", "POST"])
@acl.roles_required("admin")
@login_required
def delete(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = meeting.class_

    meeting.delete()
    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<meeting_id>/upload", methods=["GET", "POST"])
@login_required
def report(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = meeting.class_

    meeting_report = models.MeetingReport()
    meeting_report.type = "meeting"
    meeting_report.owner = current_user._get_current_object()
    meeting_report.ip_address = request.remote_addr

    meeting_report.class_ = models.Class.objects.get(id=class_.id)
    meeting_report.meeting = models.Meeting.objects.get(id=meeting_id)

    form = forms.meetings.StudentWorkMeetingForm()

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report-edit.html", meeting=meeting, class_=class_, form=form
        )

    form.populate_obj(meeting_report)
    meeting_report.save()

    return redirect(url_for("classes.view", class_id=class_.id))


@module.route("/<meeting_report_id>/edit", methods=["GET", "POST"])
@login_required
def edit_meeting_report(meeting_report_id):

    meeting_report = models.MeetingReport.objects.get(id=meeting_report_id)
    form = forms.meetings.StudentWorkMeetingForm(obj=meeting_report)

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report-edit.html",
            meeting=meeting_report.meeting,
            class_=meeting_report.class_,
            form=form,
            meeting_report=meeting_report,
        )

    meeting_report.owner = current_user._get_current_object()
    meeting_report.ip_address = request.remote_addr

    form.populate_obj(meeting_report)
    meeting_report.save()

    return redirect(url_for("classes.view", class_id=meeting_report.class_.id))
