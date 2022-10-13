from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
)
from flask_login import current_user, login_required
import mongoengine as me
import datetime

from bussaya import models
from bussaya.web import forms, acl


module = Blueprint(
    "classes",
    __name__,
    url_prefix="/classes",
)


@module.route("/")
@acl.roles_required("admin")
def index():
    classes = models.Class.objects().order_by("-id")
    return render_template("/admin/classes/index.html", classes=classes)


@module.route("/create", methods=["GET", "POST"])
@acl.roles_required("admin")
def create():
    form = forms.classes.ClassForm()
    if not form.validate_on_submit():
        return render_template("/admin/classes/create-edit.html", form=form)

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

    if not form.validate_on_submit():
        return render_template(
            "/admin/classes/create-edit.html", form=form, class_=class_
        )

    form.populate_obj(class_)
    class_.owner = current_user._get_current_object()
    class_.save()

    class_.student_ids = sorted(class_.student_ids)
    class_.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/copy")
@acl.roles_required("admin")
def copy(class_id):
    class_ = models.Class.objects.get(id=class_id)
    data = class_.to_mongo()
    data.pop("_id")
    print(data)
    new_class = models.Class(**data)
    new_class.name = f"Copy of {class_.name}"
    new_class.owner = current_user._get_current_object()
    now = datetime.datetime.now()
    new_class.created_date = now
    new_class.updated_date = now
    new_class.started_date = now.today()
    new_class.ended_date = now.today() + datetime.timedelta(days=30 * 4)
    new_class.save()

    meetings = models.Meeting.objects(class_=class_).order_by("ended_date")

    for meeting in meetings:
        data = meeting.to_mongo()
        data.pop("_id")
        new_meeting = models.Meeting(**data)
        new_meeting.created_date = now
        new_meeting.updated_date = now
        new_meeting.started_date = now + (now - meeting.started_date)
        new_meeting.ended_date = now + (now - meeting.ended_date)
        new_meeting.extended_date = now + (now - meeting.extended_date)
        new_meeting.owner = current_user._get_current_object()
        new_meeting.class_ = new_class
        new_meeting.save()

    submissions = models.Submission.objects(class_=class_)
    for submission in submissions:
        data = submission.to_mongo()
        data.pop("_id")
        new_submission = models.Submission(**data)
        new_submission.created_date = now
        new_submission.updated_date = now
        new_submission.started_date = now + (now - submission.started_date)
        new_submission.ended_date = now + (now - submission.ended_date)
        new_submission.extended_date = now + (now - submission.extended_date)
        new_submission.owner = current_user._get_current_object()
        new_submission.class_ = new_class
        new_submission.save()

    return redirect(url_for("admin.classes.view", class_id=new_class.id))


@module.route("/<class_id>", methods=["GET", "POST"])
@acl.roles_required("admin")
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    projects = models.Project.objects(class_=class_)
    submissions = models.Submission.objects(class_=class_)
    final_submission = models.FinalSubmission.objects(class_=class_).first()
    meetings = models.Meeting.objects(class_=class_)

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
        "/admin/classes/view.html",
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
        "/classes/students.html",
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
        me.Q(creator__in=students) | me.Q(students__in=students)
    )

    return render_template(
        "/classes/projects.html", class_=class_, students=students, projects=projects
    )


def get_final_report_project(project):
    final_report = models.FinalReport.objects(project=project).first()

    return final_report


@module.route("/<class_id>/final_reports")
@acl.roles_required("admin")
def view_final_reports(class_id):
    class_ = models.Class.objects.get(id=class_id)
    projects = models.Project.objects(class_=class_)

    return render_template(
        "/admin/final_reports/view.html",
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
            "/admin/final_reports/set-edit.html", class_=class_, form=form
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
            "/admin/final_reports/set-edit.html", class_=class_, form=form
        )
    form.populate_obj(final_submission)
    final_submission.class_ = class_
    final_submission.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))
