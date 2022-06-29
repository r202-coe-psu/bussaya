from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from .. import forms
from .. import models
import mongoengine as me

from bussaya import acl

import datetime
import socket

module = Blueprint("meetings", __name__, url_prefix="/meetings")


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


@module.route("/classes/<class_id>/<meeting_id>/view", methods=["GET", "POST"])
@login_required
def view(meeting_id, class_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    class_ = models.Class.objects.get(id=class_id)
    student_works = models.StudentWork.objects.all().filter(
        class_=class_, meeting=meeting
    )

    return render_template(
        "/meetings/view.html",
        meeting=meeting,
        class_=class_,
        student_works=student_works,
    )
