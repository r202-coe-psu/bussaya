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
from bussaya.web import forms, acl


module = Blueprint("projects", __name__, url_prefix="/projects")


@module.route("/<project_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def edit(project_id):
    project = models.Project.objects.get(id=project_id)

    if not project:
        return redirect("dashboard.index")

    form = forms.projects.ProjectForm(obj=project)

    lecturers = models.User.objects(roles="lecturer").order_by("first_name")
    form.advisors.queryset = lecturers
    form.committees.queryset = lecturers

    # classes = models.Class.objects(student_ids=current_user.username).order_by("-id")

    students = models.User.objects(username__regex="^[0-9]*$").order_by("-username")
    form.students.queryset = students

    if not form.validate_on_submit():
        return render_template("/projects/create-edit.html", form=form)

    form.populate_obj(project)
    for advisor in project.advisors:
        if advisor in project.committees:
            project.committees.remove(advisor)
    # project.creator = current_user._get_current_object()

    project.save()
    class_id = request.args.get("class_id")
    if class_id:
        return redirect(url_for("admin.classes.view_projects", class_id=class_id))

    return redirect(url_for("dashboard.index"))


@module.route("/<project_id>/delete")
@acl.roles_required("admin")
def delete(project_id):
    project = models.Project.objects.get(id=project_id)

    for resource in project.resources:
        if resource.data:
            resource.data.delete()

    project.delete()

    return redirect(request.referrer)
