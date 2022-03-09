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
    "classes",
    __name__,
    url_prefix="/classes",
)


@module.route("/")
@acl.admin_permission.require(http_exception=403)
def index():
    classes = models.Class.objects()
    return render_template("/admin/classes/index.html", classes=classes)


@module.route("/create", methods=["GET", "POST"])
@acl.admin_permission.require(http_exception=403)
def create():
    form = forms.classes.ClassForm()
    if not form.validate_on_submit():
        return render_template("/admin/classes/create-edit.html", form=form)

    class_ = models.Class()
    form.populate_obj(class_)
    class_.owner = current_user._get_current_object()
    class_.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>/edit", methods=["GET", "POST"])
@acl.admin_permission.require(http_exception=403)
def edit(class_id):
    class_ = models.Class.objects.get(id=class_id)

    form = forms.classes.ClassForm()
    if request.method == "GET":
        form = forms.classes.ClassForm(obj=class_)

    if not form.validate_on_submit():
        return render_template("/admin/classes/create-edit.html", form=form)

    form.populate_obj(class_)
    class_.owner = current_user._get_current_object()
    class_.save()

    return redirect(url_for("admin.classes.view", class_id=class_.id))


@module.route("/<class_id>")
@acl.admin_permission.require(http_exception=403)
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    projects = models.Project.objects(class_=class_)
    return render_template(
        "/admin/classes/view.html",
        class_=class_,
        projects=projects,
    )
