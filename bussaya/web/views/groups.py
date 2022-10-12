from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
)
from flask_login import current_user, login_required

from .projects import populate_obj
from bussaya import models
from .. import forms, acl

module = Blueprint(
    "groups",
    __name__,
    url_prefix="/groups",
)


def get_student_ids(group):
    sorted_student_ids = [student.username for student in group.students]
    return ", ".join(sorted_student_ids)


@module.route("/<class_id>/view")
@acl.roles_required("lecturer")
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    groups = models.Group.objects.all().filter(class_=class_)

    return render_template(
        "/groups/view.html",
        class_=class_,
        groups=groups,
        get_student_ids=get_student_ids,
    )
