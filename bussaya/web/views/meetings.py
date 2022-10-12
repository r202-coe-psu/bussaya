from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user

from bussaya.models.submissions import MeetingReport
import mongoengine as me
import markdown

import datetime
import socket

from bussaya import models
from bussaya.web import acl, forms


module = Blueprint("meetings", __name__, url_prefix="/meetings")


@module.route("/<meeting_id>/", methods=["GET", "POST"])
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

    meeting_reports = list(meeting_reports)
    meeting_reports.sort(key=lambda r: r.owner.username)
    return render_template(
        "/admin/meetings/view.html",
        meeting=meeting,
        class_=meeting.class_,
        meeting_reports=meeting_reports,
        form=form,
        markdown=markdown,
    )


@module.route("/<meeting_id>/view/lecturer", methods=["GET", "POST"])
@login_required
def view_lecturer(meeting_id):
    meeting = models.Meeting.objects.get(id=meeting_id)
    students = models.User.objects(username__in=meeting.class_.student_ids)
    projects = models.Project.objects(
        me.Q(advisor=current_user._get_current_object())
        & (me.Q(creator__in=students) | me.Q(students__in=students))
    )
    meeting_reports = models.MeetingReport.objects(
        class_=meeting.class_, meeting=meeting, project__in=projects
    ).order_by("-owner.username")

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

    meeting_reports = list(meeting_reports)
    meeting_reports.sort(key=lambda r: r.owner.username)
    return render_template(
        "/meetings/view.html",
        meeting=meeting,
        class_=meeting.class_,
        meeting_reports=meeting_reports,
        form=form,
        markdown=markdown,
    )


@module.route(
    "/<meeting_id>/reports/<meeting_report_id>/approval/<action>",
    methods=["GET", "POST"],
)
@acl.roles_required("lecturer")
def approval(meeting_id, meeting_report_id, action):

    meeting_report = models.MeetingReport.objects.get(id=meeting_report_id)
    if meeting_report.project.advisor != current_user._get_current_object():
        return redirect(url_for("dashboard.index"))

    form = forms.meetings.DisapproveForm()

    if action == "approve":
        meeting_report.status = "approved"
    elif action == "disapprove":
        meeting_report.status = "disapproved"
        meeting_report.remark += f"\n\n{form.remark.data}"

    meeting_report.approver = current_user._get_current_object()
    meeting_report.approved_date = datetime.datetime.now()
    meeting_report.approver_ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )
    meeting_report.save()

    return redirect(request.referrer)


@module.route(
    "/create/<class_id>/<name>/<round>/<start>/<end>", methods=["GET", "POST"]
)
@acl.roles_required("admin")
def create(class_id, name, round, start, end):
    class_ = models.Class.objects.get(id=class_id)

    meeting = models.Meeting()
    meeting.name = name
    meeting.round = round
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

    form = forms.meetings.MeetingForm(obj=meeting)

    if request.method != "POST":
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


@module.route(
    "/<meeting_id>/reports/create",
    methods=["GET", "POST"],
    defaults=dict(meeting_report_id=""),
)
@module.route("/<meeting_id>/reports/<meeting_report_id>/edit", methods=["GET", "POST"])
@login_required
def report(meeting_id, meeting_report_id):
    meeting = models.Meeting.objects.get(id=meeting_id)

    if meeting.get_status() == "closed":
        return redirect(url_for("classes.view", class_id=class_.id))

    meeting_report = None
    if meeting_report_id:
        meeting_report = models.MeetingReport.objects(id=meeting_report_id).first()
    class_ = meeting.class_
    projects = models.Project.objects(
        me.Q(creator=current_user._get_current_object())
        | me.Q(students=current_user._get_current_object())
    ).order_by("name")

    form = forms.meetings.MeetingReportForm(obj=meeting_report)
    form.project.queryset = projects

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report.html",
            projects=projects,
            meeting=meeting,
            class_=class_,
            form=form,
            meeting_report=meeting_report,
        )

    if not meeting_report:
        meeting_report = models.MeetingReport()
        meeting_report.owner = current_user._get_current_object()

        meeting_report.class_ = meeting.class_
        meeting_report.meeting = meeting

    form.populate_obj(meeting_report)
    meeting_report.updated_date = datetime.datetime.now()
    meeting_report.owner = current_user._get_current_object()
    meeting_report.ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )

    meeting_report.save()

    return redirect(url_for("classes.view", class_id=class_.id))


@module.route(
    "/<meeting_id>/reports/late-report",
    methods=["GET", "POST"],
    defaults=dict(meeting_report_id=""),
)
@module.route(
    "/<meeting_id>/reports/<meeting_report_id>/edit-late-report",
    methods=["GET", "POST"],
)
@login_required
def late_report(meeting_id, meeting_report_id):
    meeting = models.Meeting.objects.get(id=meeting_id)

    meeting_report = None
    if meeting_report_id:
        meeting_report = models.MeetingReport.objects(id=meeting_report_id).first()

    class_ = meeting.class_
    projects = models.Project.objects(
        me.Q(creator=current_user._get_current_object())
        | me.Q(students=current_user._get_current_object())
    ).order_by("name")

    form = forms.meetings.LateMeetingReportForm(obj=meeting_report)
    form.project.queryset = projects

    if not form.validate_on_submit():
        return render_template(
            "/meetings/report.html",
            projects=projects,
            meeting=meeting,
            class_=class_,
            form=form,
            meeting_report=meeting_report,
        )

    if not meeting_report:
        meeting_report = models.MeetingReport()
        meeting_report.owner = current_user._get_current_object()

        meeting_report.class_ = meeting.class_
        meeting_report.meeting = meeting
        meeting_report.status = "late-report"

    form.populate_obj(meeting_report)
    meeting_report.updated_date = datetime.datetime.now()
    meeting_report.owner = current_user._get_current_object()
    meeting_report.ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )

    meeting_report.save()

    return redirect(url_for("classes.view", class_id=class_.id))


@module.route(
    "/<meeting_id>/reports/admin-force-create",
    methods=["GET", "POST"],
    defaults=dict(meeting_report_id=""),
)
@module.route(
    "/<meeting_id>/reports/<meeting_report_id>/admin-force-edit",
    methods=["GET", "POST"],
)
@acl.roles_required("admin")
def force_report(meeting_id, meeting_report_id):
    meeting = models.Meeting.objects.get(id=meeting_id)

    meeting_report = None
    if meeting_report_id:
        meeting_report = models.MeetingReport.objects(id=meeting_report_id).first()

    class_ = meeting.class_
    students = class_.get_students()

    projects = models.Project.objects(
        me.Q(creator__in=students) | me.Q(students__in=students)
    ).order_by("name")

    form = forms.meetings.AdminMeetingReportForm(obj=meeting_report)
    form.project.queryset = projects
    form.student.choices = [
        (str(s.id), f"{s.username} - {s.first_name} {s.last_name}") for s in students
    ]
    form.student.choices.sort()

    if not form.validate_on_submit():
        return render_template(
            "/admin/meetings/report.html",
            projects=projects,
            meeting=meeting,
            class_=class_,
            form=form,
            meeting_report=meeting_report,
        )

    if not meeting_report:
        meeting_report = models.MeetingReport()
        meeting_report.owner = models.User.objects.get(id=form.student.data)

        meeting_report.class_ = meeting.class_
        meeting_report.meeting = meeting

    form.populate_obj(meeting_report)
    meeting_report.updated_date = datetime.datetime.now()
    meeting_report.owner = models.User.objects.get(id=form.student.data)
    meeting_report.ip_address = request.headers.get(
        "X-Forwarded-For", request.remote_addr
    )

    meeting_report.save()

    return redirect(url_for("meetings.view_admin", meeting_id=meeting_id))
