from flask import Blueprint, render_template, redirect

from bussaya import acl, models


module = Blueprint("admin", __name__, url_prefix="/admin")


@module.route("/")
@acl.roles_required("admin")
def index():
    class_ = models.Class.objects().order_by("-id").first()

    if class_ is None:
        return redirect("dashboard.index")

    projects = models.Project.objects(class_=class_)

    return render_template("/admin/index.html", class_=class_, projects=projects)
