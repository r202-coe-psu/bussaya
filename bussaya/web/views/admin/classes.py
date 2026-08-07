from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
    flash,
)
from flask_login import current_user, login_required
import mongoengine as me
import datetime

from bussaya import models
from bussaya.web import forms, acl

from .. import classes

module = Blueprint(
    "classes",
    __name__,
    url_prefix="/classes",
)


@module.route("/")
@acl.roles_required("admin")
def index():
    classes = models.Class.objects().order_by("-id")
    return render_template("/admin/classes/index.html.j2", classes=classes)


@module.route("/create", methods=["GET", "POST"])
@acl.roles_required("admin")
def create():
    form = forms.classes.ClassForm()
    form.curriculum.queryset = models.Curriculum.objects(status="active").order_by("name")
    if not form.validate_on_submit():
        return render_template("/admin/classes/create-edit.html.j2", form=form)

    class_ = models.Class()
    form.populate_obj(class_)
    class_.owner = current_user._get_current_object()
    class_.save()

    class_.student_ids = sorted(class_.student_ids)
    class_.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def edit(class_id):
    class_ = models.Class.objects.get(id=class_id)

    form = forms.classes.ClassForm()
    if request.method == "GET":
        form = forms.classes.ClassForm(obj=class_)
    form.curriculum.queryset = models.Curriculum.objects(status="active").order_by("name")

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/create-edit.html.j2", form=form, class_=class_
        )

    form.populate_obj(class_)
    class_.owner = current_user._get_current_object()
    class_.save()

    class_.student_ids = sorted(class_.student_ids)
    class_.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/copy", methods=["GET", "POST"])
@acl.roles_required("admin")
def copy(class_id):
    old_class = models.Class.objects.get(id=class_id)

    form = forms.classes.ClassForm(obj=old_class)
    form.curriculum.queryset = models.Curriculum.objects(status="active").order_by("name")
    if not form.validate_on_submit():
        if request.method == "GET":
            form.name.data = f"Copy of {form.name.data}"
            form.started_date.data = datetime.datetime.today()
            form.ended_date.data = form.started_date.data + datetime.timedelta(weeks=18)


        return render_template(
            "/admin/classes/create-edit.html.j2", form=form, class_=old_class
        )

    new_class = models.Class()
    form.populate_obj(new_class)
    new_class.owner = current_user._get_current_object()
    new_class.save()

    new_class.student_ids = sorted(old_class.student_ids)
    new_class.save()

    meetings = models.Meeting.objects(class_=old_class).order_by("started_date")

    new_class_started_date = datetime.datetime.combine(
        new_class.started_date, datetime.datetime.min.time()
    )
    old_class_started_date = datetime.datetime.combine(
        old_class.started_date, datetime.datetime.min.time()
    )
    for meeting in meetings:
        data = meeting.to_mongo()
        data.pop("_id")
        data.pop("created_date")
        data.pop("updated_date")
        new_meeting = models.Meeting(**data)
        new_meeting.started_date = new_class_started_date + (
            meeting.started_date - old_class_started_date
        )
        new_meeting.ended_date = new_class_started_date + (
            meeting.ended_date - old_class_started_date
        )
        new_meeting.extended_date = new_class_started_date + (
            meeting.extended_date - old_class_started_date
        )
        new_meeting.owner = current_user._get_current_object()
        new_meeting.class_ = new_class
        new_meeting.save()

    submissions = models.Submission.objects(class_=old_class)
    for submission in submissions:
        data = submission.to_mongo()
        data.pop("_id")
        data.pop("created_date")
        data.pop("updated_date")
        new_submission = models.Submission(**data)
        new_submission.started_date = new_class_started_date + (
            submission.started_date - old_class_started_date
        )
        new_submission.ended_date = new_class_started_date + (
            submission.ended_date - old_class_started_date
        )
        new_submission.extended_date = new_class_started_date + (
            submission.extended_date - old_class_started_date
        )
        new_submission.owner = current_user._get_current_object()
        new_submission.class_ = new_class
        new_submission.save()

    return redirect(url_for("admin.classes.view", class_id=new_class.id))


@module.route("/<class_id>", methods=["GET", "POST"])
@acl.roles_required("admin")
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    projects = models.Project.objects(class_=class_, status="active")
    submissions = models.Submission.objects(class_=class_)
    final_submission = models.FinalSubmission.objects(class_=class_).first()
    meetings = models.Meeting.objects(class_=class_).order_by("ended_date")

    form = forms.meetings.MeetingForm()
    if form.validate_on_submit():
        return redirect(
            url_for(
                "meetings.create",
                class_id=class_.id,
                name=form.name.data,
                round=form.round.data,
                start=form.started_date.data,
                end=form.ended_date.data,
            )
        )

    return render_template(
        "/admin/classes/view.html.j2",
        form=form,
        class_=class_,
        class_id=class_id,
        projects=projects,
        submissions=submissions,
        final_submission=final_submission,
        meetings=meetings,
    )


@module.route("/<class_id>/delete")
@acl.roles_required("admin")
def delete(class_id):
    class_ = models.Class.objects.get(id=class_id)
    class_.delete()

    return redirect(url_for("admin.classes.index", class_id=class_id))


def get_student_by_id(student_id, students):
    for s in students:
        if s.username == student_id:
            return s

    return None


@module.route("/<class_id>/students")
@acl.roles_required("admin")
def view_students(class_id):
    class_ = models.Class.objects.get(id=class_id)
    students = models.User.objects(username__in=class_.student_ids).order_by(
        "-username"
    )

    return render_template(
        "/classes/students.html.j2",
        class_=class_,
        students=students,
        get_student_by_id=get_student_by_id,
    )


@module.route("/<class_id>/projects")
@acl.roles_required("admin")
def view_projects(class_id):
    class_ = models.Class.objects.get(id=class_id)
    students = models.User.objects(username__in=class_.student_ids).order_by(
        "-username"
    )
    projects = models.Project.objects(
        me.Q(creator__in=students) | me.Q(students__in=students), status="active"
    )

    return render_template(
        "/classes/projects.html.j2", class_=class_, students=students, projects=projects
    )


def get_final_report_project(project):
    final_report = models.FinalReport.objects(project=project).first()

    return final_report


@module.route("/<class_id>/final_reports")
@acl.roles_required("admin")
def view_final_reports(class_id):
    class_ = models.Class.objects.get(id=class_id)
    projects = models.Project.objects(class_=class_, status="active")

    return render_template(
        "/admin/final_reports/view.html.j2",
        class_=class_,
        projects=projects,
        get_final_report_project=get_final_report_project,
    )


@module.route("/<class_id>/final_submission/set", methods=["GET", "POST"])
@acl.roles_required("admin")
def set_final_submission(class_id):
    class_ = models.Class.objects.get(id=class_id)
    form = forms.submissions.FinalSubmissionForm()
    if not form.validate_on_submit():
        return render_template(
            "/admin/final_reports/set-edit.html.j2", class_=class_, form=form
        )

    final_submission = models.submissions.FinalSubmission()
    form.populate_obj(final_submission)
    final_submission.class_ = class_
    final_submission.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route(
    "/<class_id>/final_submission/<final_submission_id>/edit", methods=["GET", "POST"]
)
@acl.roles_required("admin")
def edit_final_submission(class_id, final_submission_id):
    class_ = models.Class.objects.get(id=class_id)
    final_submission = models.submissions.FinalSubmission(id=final_submission_id)

    form = forms.submissions.FinalSubmissionForm(obj=final_submission)
    if not form.validate_on_submit():
        return render_template(
            "/admin/final_reports/set-edit.html.j2", class_=class_, form=form
        )
    form.populate_obj(final_submission)
    final_submission.class_ = class_
    final_submission.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/students/approve-meeting-reports")
@acl.roles_required("admin")
def approve_meeting_report(class_id):
    return classes.approve_meeting_report(class_id)


@module.route("/<class_id>/force-add-meeting-report", methods=["GET", "POST"])
@acl.roles_required("admin")
def force_add_meeting_report(class_id):
    class_ = models.Class.objects.get(id=class_id)
    students = class_.get_students()

    form = forms.meetings.ForceAddMeetingReportForm()
    form.student.choices = [
        (str(s.id), f"{s.username} - {s.first_name} {s.last_name}")
        for s in sorted(students, key=lambda s: s.username)
    ]

    if not form.validate_on_submit():
        flash("Failed to force add meeting report. Please check input.", "error")
        return redirect(
            url_for(
                "admin.classes.approve_meeting_report",
                class_id=class_.id,
                admin_view="true",
            )
        )

    student = models.User.objects.get(id=form.student.data)
    project = student.get_project()
    meeting_date = form.meeting_date.data

    # Automatic meeting schedule matching by date
    matched_meeting = None
    meetings = models.Meeting.objects(class_=class_).order_by("started_date")
    for m in meetings:
        start_d = m.started_date.date()
        end_d = m.extended_date.date() if m.extended_date else m.ended_date.date()
        if start_d <= meeting_date <= end_d:
            matched_meeting = m
            break

    if not matched_meeting and meetings:
        matched_meeting = min(
            meetings, key=lambda m: abs((m.started_date.date() - meeting_date).days)
        )

    meeting_report = models.MeetingReport(
        owner=student,
        class_=class_,
        project=project,
        meeting=matched_meeting,
        title=form.title.data,
        description=form.description.data or "",
        meeting_date=meeting_date,
        status="approved",
        approver=current_user._get_current_object(),
        approved_date=datetime.datetime.now(),
        remark=form.remark.data or "Force added by admin",
        advisors=project.advisors if project else [],
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
    )

    if form.uploaded_file.data:
        meeting_report.file.put(
            form.uploaded_file.data,
            filename=form.uploaded_file.data.filename,
            content_type=form.uploaded_file.data.content_type,
        )

    meeting_report.save()

    meeting_name = matched_meeting.name if matched_meeting else "N/A"
    flash(
        f"Meeting report '{meeting_report.title}' force added for {student.first_name} {student.last_name} and automatically matched to meeting '{meeting_name}'.",
        "success",
    )

    return redirect(
        url_for(
            "admin.classes.approve_meeting_report",
            class_id=class_.id,
            admin_view="true",
        )
    )
