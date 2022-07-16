from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user

from bussaya.models.submissions import StudentWork
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
    student_works = models.StudentWork.objects.all().filter(
        class_=meeting.class_, meeting=meeting
    )

    form = forms.meetings.DisapproveForm()

    if request.method == "POST":
        student_work = models.StudentWork.objects.get(
            id=request.form.get("student_work_id")
        )
        student_work.remark = form.remark.data
        student_work.save()

        approval(
            meeting_id=meeting.id, student_work_id=student_work.id, action="disapproved"
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

    student_work = models.StudentWork.objects.get(id=student_work_id)
    student_work.status = action
    if action == "approved":
        student_work.remark = None

    student_work.save()

    return redirect(url_for("meetings.view", meeting_id=meeting_id))


@module.route("/<class_id>/<meeting_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
@login_required
def edit(class_id, meeting_id):
    class_ = models.Class.objects.get(id=class_id)
    meeting = models.Meeting.objects.get(id=meeting_id)
    form = forms.meetings.MeetingForm()

    if request.method == "GET":
        form = forms.meetings.MeetingForm(obj=meeting)

    if not form.validate_on_submit():
        return render_template("/meetings/edit.html", class_=class_, form=form)

    form.populate_obj(meeting)
    meeting.save()
    return redirect(url_for("admin.classes.view", class_id=class_id))


@module.route("/<class_id>/<meeting_id>/delete", methods=["GET", "POST"])
@acl.roles_required("admin")
@login_required
def delete(class_id, meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    meeting.delete()
    return redirect(url_for("admin.classes.view", class_id=class_id))


@module.route("/classes/<class_id>/<meeting_id>/upload", methods=["GET", "POST"])
@login_required
def report(meeting_id, class_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = models.Class.objects.get(id=class_id)

    student_work = models.StudentWork()
    student_work.type = "meeting"
    student_work.owner = current_user._get_current_object()
    student_work.ip_address = request.remote_addr

    student_work.class_ = models.Class.objects.get(id=class_id)
    student_work.meeting = models.Meeting.objects.get(id=meeting_id)

    form = forms.meetings.StudentWorkMeetingForm()

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report-edit.html", meeting=meeting, class_=class_, form=form
        )

    form.populate_obj(student_work)
    student_work.save()

    return redirect(url_for("classes.view", class_id=class_.id))


@module.route("/classes/<class_id>/<meeting_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student_work(meeting_id, class_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = models.Class.objects.get(id=class_id)

    student_work = models.StudentWork.objects.get(class_=class_, meeting=meeting)
    form = forms.meetings.StudentWorkMeetingForm(obj=student_work)

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report-edit.html",
            meeting=meeting,
            class_=class_,
            form=form,
            student_work=student_work,
        )

    student_work.owner = current_user._get_current_object()
    student_work.ip_address = request.remote_addr

    form.populate_obj(student_work)
    student_work.save()

    return redirect(url_for("classes.view", class_id=class_.id))
