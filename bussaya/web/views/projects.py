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


module = Blueprint("projects", __name__, url_prefix="/projects")


@module.route("/")
def index():
    # need implement
    return redirect(url_for("tags.index"))


def populate_obj(form, project):
    form.populate_obj(project)
    # project.class_ = models.Class.objects.get(id=form.class_.data)
    # project.advisor = models.User.objects.get(id=form.advisor.data)
    # project.committees = [
    # models.User.objects.get(id=uid) for uid in form.committees.data
    # ]
    for advisor in project.advisors:
        if advisor in project.committees:
            project.committees.remove(advisor)

    project.creator = current_user._get_current_object()

    if current_user._get_current_object() not in project.students:
        project.students.append(current_user._get_current_object())

    # project.students = [current_user._get_current_object()]
    # if form.contributors.data and len(form.contributors.data) > 0:
    #     contributor = models.User.objects.get(id=form.contributors.data)
    #     if contributor not in project.students:
    #         project.students.append(contributor)


def get_project_form(project=None):
    form = forms.projects.ProjectForm()

    if project:
        form = forms.projects.ProjectForm(obj=project)

    lecturers = models.User.objects(roles="CoE-lecturer").order_by("first_name")
    form.advisors.queryset = lecturers
    form.committees.queryset = lecturers

    classes = models.Class.objects(student_ids=current_user.username).order_by("-id")

    students = models.User.objects(username__regex="^[0-9]*$").order_by("-username")
    form.students.queryset = students

    # if project and request.method == "GET":
    #     form.advisor.data = str(project.advisor.id)
    #     form.committees.data = [str(c.id) for c in project.committees]
    #     contributors = project.students
    #     contributors.remove(current_user._get_current_object())
    #     if len(contributors) > 0:
    #         form.contributors.data = str(contributors[0].id)

    return form


@module.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = get_project_form()
    if not form.validate_on_submit():
        return render_template("/projects/create-edit.html", form=form)

    project = models.Project()
    populate_obj(form, project)
    project.save()

    return redirect(url_for("dashboard.index"))


@module.route("/<project_id>/edit", methods=["GET", "POST"])
@login_required
def edit(project_id):
    project = models.Project.objects.get(id=project_id)
    form = get_project_form(project)

    if not form.validate_on_submit():
        return render_template("/projects/create-edit.html", form=form)

    populate_obj(form, project)
    project.save()

    return redirect(url_for("dashboard.index"))


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


@module.route("/<project_id>/upload", methods=["GET", "POST"])
@login_required
def upload(project_id):
    project = models.Project.objects.get(id=project_id)
    if current_user._get_current_object() not in project.students:
        response = Response()
        response.status_code = 403
        return response

    form = forms.projects.ProjectResourceUploadForm()
    if not form.validate_on_submit():
        return render_template("/projects/upload.html", form=form, project=project)

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
        resource = get_resource(f, t, project_id)
        project.resources.append(resource)

    files = [form.video.data, form.git.data]
    types = ["video", "git"]
    for f, t in zip(files, types):
        if not f:
            continue
        resource = models.ProjectResource(type=t, link=f)
        project.resources.append(resource)
    project.save()

    return redirect(url_for("dashboard.index"))


@module.route("/<project_id>/approve")
@login_required
def approve(project_id):
    project = models.Project.objects.get(id=project_id)
    user = current_user._get_current_object()
    if user not in project.committees and user != project.advisor:
        response = Response()
        response.status_code = 403
        return response

    for approval in project.approvals:
        if approval.committee == user:
            return redirect(url_for("dashboard.index"))

    approval = models.ProjectApproval(committee=user, type="approve")
    project.approvals.append(approval)
    project.save()

    return redirect(url_for("dashboard.index"))


@module.route("/<project_id>/resources/<resource_id>/<filename>")
def download(project_id, resource_id, filename):
    project = models.Project.objects.get(id=project_id)
    response = Response()
    response.status_code = 404

    if not project:
        return response

    resources = reversed(project.resources)
    resource = None
    for r in resources:
        if str(r.id) == resource_id and r.data.filename == filename:
            resource = r
            break

    if not resource:
        return resource

    now = datetime.datetime.now()
    election = models.Election.objects(
        started_date__lte=now, ended_date__gte=now
    ).first()
    if not election and current_user.is_anonymous:
        if resource.type not in project.public:
            response.status_code = 403
            return response

    response = send_file(
        resource.data,
        download_name=resource.data.filename,
        # as_attachment=True,
        mimetype=resource.data.content_type,
    )

    return response


@module.route("/<project_id>")
def view(project_id):
    project = models.Project.objects.get(id=project_id)
    return render_template(
        "/projects/view.html",
        project=project,
    )


@module.route("/<project_id>/view-project-info", methods=["GET", "POST"])
def view_info_project(project_id):
    project = models.Project.objects.get(id=project_id)

    return render_template("/projects/view-info-projects.html", project=project)
