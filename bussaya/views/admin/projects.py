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

from bussaya import forms
from bussaya import models
from bussaya import acl


module = Blueprint("projects", __name__, url_prefix="/projects")


@module.route("/<project_id>/delete")
@acl.roles_required("admin")
def delete(project_id):
    project = models.Project.objects.get(id=project_id)

    for resource in project.resources:
        if resource.data:
            resource.data.delete()

    project.delete()

    return redirect(request.referrer)
