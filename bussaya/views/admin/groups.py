from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    request,
)
from flask_login import current_user, login_required

from bussaya import models, forms, acl
from bussaya.views.projects import populate_obj

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


def get_group_form(group=None):
    form = forms.groups.GroupForm(obj=group)
    if group:
        students = group.students
        form.students.data = [student.username for student in students]
        form.committees.data = [str(lec.id) for lec in group.committees]

    lecturers = models.User.objects(roles="lecturer").order_by("first_name")
    lec_choices = [(str(l.id), f"{l.first_name} {l.last_name}") for l in lecturers]
    form.committees.choices = lec_choices
    return form


@module.route("/<class_id>/set_group_student_ids")
@acl.roles_required("admin")
def set_group_student_ids(class_id):
    groups = models.Group.objects.all().filter(
        class_=models.Class.objects.get(id=class_id)
    )
    class_ = models.Class.objects.get(id=class_id)
    for group in groups:
        group.students = []

        print([lec.first_name for lec in group.committees])
        projects = models.Project.objects.all().filter(
            advisor__in=group.committees, class_=class_
        )

        for project in projects:
            print([lec.first_name for lec in project.committees])
            for student in project.students:
                if student.username in class_.student_ids:
                    if student not in group.students:
                        group.students.append(student)

        group.students.sort(key=lambda s: s.username)
        group.save()

    return redirect(url_for("admin.groups.manage", class_id=class_id))


def get_student_ids(group):
    sorted_student_ids = [student.username for student in group.students]
    return ", ".join(sorted_student_ids)


@module.route("/<class_id>/manage", methods=["GET", "POST"])
@acl.roles_required("admin")
def manage(class_id):
    class_ = models.Class.objects.get(id=class_id)
    groups = models.Group.objects.all().filter(class_=class_)

    form = get_group_form()
    if form.validate_on_submit():
        group = models.Group()
        form.populate_obj(group)
        group.class_ = class_
        group.committees = [
            models.User.objects.get(id=uid) for uid in form.committees.data
        ]
        group.save()

        return redirect(url_for("admin.groups.manage", class_id=class_.id))

    return render_template(
        "/admin/groups/manage.html",
        class_=class_,
        groups=groups,
        form=form,
        get_student_ids=get_student_ids,
    )


@module.route("/<class_id>/<group_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def edit(class_id, group_id):
    class_ = models.Class.objects.get(id=class_id)
    group = models.Group.objects.get(id=group_id)
    form = get_group_form()

    if request.method == "GET":
        form = get_group_form(group)

    if not form.validate_on_submit():
        return render_template("/admin/groups/edit.html", class_=class_, form=form)

    form.populate_obj(group)
    group.committees = [models.User.objects.get(id=uid) for uid in form.committees.data]
    group.students = [
        models.User.objects.get(username=student_id)
        for student_id in form.students.data
    ]
    group.save()
    return redirect(url_for("admin.groups.manage", class_id=class_id))


@module.route("/<class_id>/<group_id>/delete", methods=["GET", "POST"])
@acl.roles_required("admin")
def delete(class_id, group_id):
    group = models.Group.objects.get(id=group_id)
    group.delete()

    return redirect(url_for("admin.groups.manage", class_id=class_id))
