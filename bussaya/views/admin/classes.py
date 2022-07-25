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


@module.route("/<class_id>/home", methods=["GET", "POST"])
@acl.roles_required("admin")
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    projects = models.Project.objects(class_=class_)
    submissions = models.Submission.objects(class_=class_)
    meetings = models.Meeting.objects(class_=class_)

    form = forms.meetings.MeetingForm()
    if form.validate_on_submit():
        return redirect(
            url_for(
                "meetings.create",
                class_id=class_.id,
                name=form.name.data,
                grade=form.grade.data,
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
        meetings=meetings,
    )


@module.route("/<class_id>/delete")
@acl.roles_required("admin")
def delete(class_id):
    class_ = models.Class.objects.get(id=class_id)
    class_.delete()

    return redirect(url_for("admin.classes.index", class_id=class_id))
