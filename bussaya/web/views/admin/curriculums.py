import datetime
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

from bussaya import models
from bussaya.web import forms, acl


module = Blueprint("curriculums", __name__, url_prefix="/curriculums")


@module.route("")
@acl.roles_required("admin")
def index():
    curriculums = models.Curriculum.objects(status="active").order_by("name")

    return render_template(
        "admin/curriculums/index.html.j2", curriculums=curriculums
    )


@module.route("/create", methods=["GET", "POST"], defaults=dict(curriculum_id=None))
@module.route("/<curriculum_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(curriculum_id):
    form = forms.curriculums.CurriculumForm()

    curriculum = None

    if curriculum_id:
        curriculum = models.Curriculum.objects.get(id=curriculum_id)
        form = forms.curriculums.CurriculumForm(obj=curriculum)

    if not form.validate_on_submit():
        return render_template(
            "admin/curriculums/create-or-edit.html.j2",
            form=form,
            curriculum=curriculum,
        )

    if not curriculum:
        curriculum = models.Curriculum()
        curriculum.created_date = datetime.datetime.now()
        curriculum.status = "active"
        curriculum.creator = current_user._get_current_object()

    form.populate_obj(curriculum)
    curriculum.updated_date = datetime.datetime.now()
    curriculum.last_updated_by = current_user._get_current_object()
    curriculum.save()

    return redirect(url_for("admin.curriculums.view", curriculum_id=curriculum.id))


@module.route("/<curriculum_id>")
@acl.roles_required("admin")
def view(curriculum_id):
    curriculum = models.Curriculum.objects(id=curriculum_id, status="active").first()

    if not curriculum:
        return redirect(url_for("admin.curriculums.index"))

    return render_template(
        "admin/curriculums/view.html.j2", curriculum=curriculum
    )


@module.route(
    "/<curriculum_id>/plos/add",
    methods=["GET", "POST"],
    defaults=dict(plo_id=None),
)
@module.route("/<curriculum_id>/plos/<plo_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_or_edit_plo(curriculum_id, plo_id):
    curriculum = models.Curriculum.objects.get(id=curriculum_id)

    form = forms.curriculums.PLOForm()
    plo = None

    if plo_id:
        plo = models.PLO.objects.get(id=plo_id)
        form = forms.curriculums.PLOForm(obj=plo)

    if not form.validate_on_submit():
        return render_template(
            "admin/curriculums/add-or-edit-plo.html.j2",
            form=form,
            plo=plo,
            curriculum=curriculum,
        )

    if not plo:
        plo = models.PLO()
        plo.created_date = datetime.datetime.now()
        plo.status = "active"
        plo.curriculum = curriculum

    form.populate_obj(plo)
    plo.updated_date = datetime.datetime.now()
    plo.save()

    return redirect(url_for("admin.curriculums.view", curriculum_id=curriculum.id))
