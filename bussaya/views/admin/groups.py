from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
)
from flask_login import current_user, login_required

from bussaya import models, forms, acl

module = Blueprint(
    "groups",
    __name__,
    url_prefix="/groups",
)


@module.route("/<class_id>")
@acl.roles_required("admin")
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)

    return render_template("/admin/grades/index.html", class_=class_)
