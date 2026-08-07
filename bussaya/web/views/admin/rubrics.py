from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user

from bussaya import models
from bussaya.web import forms, acl


module = Blueprint("rubrics", __name__, url_prefix="/rubrics")


def get_clo_choices(curriculums):
    clos = models.CLO.objects(curriculum__in=curriculums, status="active").order_by(
        "curriculum", "order"
    )
    return [
        (
            str(clo.id),
            f"[{clo.curriculum.code if clo.curriculum else ''}] {clo.get_label()}",
        )
        for clo in clos
    ]


@module.route("")
@acl.roles_required("admin")
def index():
    templates = models.RubricTemplate.objects().order_by("class_type", "-version")

    return render_template("admin/rubrics/index.html.j2", templates=templates)


@module.route("/create", methods=["GET", "POST"], defaults=dict(template_id=None))
@module.route("/<template_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(template_id):
    template = None

    if template_id:
        template = models.RubricTemplate.objects.get(id=template_id)

    form = forms.rubrics.RubricTemplateForm()
    curriculums = models.Curriculum.objects(status="active").order_by("name")
    form.curriculums.choices = [(str(c.id), c.name) for c in curriculums]

    if request.method == "GET" and template:
        form.name.data = template.name
        form.class_type.data = template.class_type
        form.description.data = template.description
        form.curriculums.data = [str(c.id) for c in template.curriculums]

    if not form.validate_on_submit():
        return render_template(
            "admin/rubrics/create-or-edit.html.j2", form=form, template=template
        )

    if not template:
        template = models.RubricTemplate()
        template.creator = current_user._get_current_object()

    template.name = form.name.data
    template.class_type = form.class_type.data
    template.description = form.description.data
    template.curriculums = list(
        models.Curriculum.objects(id__in=form.curriculums.data)
    )
    template.save()

    return redirect(url_for("admin.rubrics.criteria", template_id=template.id))


@module.route("/<template_id>/criteria", methods=["GET", "POST"])
@acl.roles_required("admin")
def criteria(template_id):
    template = models.RubricTemplate.objects.get(id=template_id)

    form = forms.rubrics.RubricCriterionForm()
    form.clos.choices = get_clo_choices(template.curriculums)

    if not form.validate_on_submit():
        return render_template(
            "admin/rubrics/criteria.html.j2", template=template, form=form
        )

    clos = models.CLO.objects(id__in=form.clos.data)
    level_explanations = []
    for level, field_name in forms.rubrics.LEVEL_FIELD_MAP:
        exp = getattr(form, field_name).data or ""
        level_explanations.append(
            models.RubricLevelExplanation(level=level, explanation=exp)
        )

    template.criteria.append(
        models.RubricCriterion(
            name=form.name.data,
            description=form.description.data,
            max_score=form.max_score.data,
            clos=list(clos),
            order=len(template.criteria),
            level_explanations=level_explanations,
        )
    )
    template.save()

    return redirect(url_for("admin.rubrics.criteria", template_id=template.id))


@module.route("/<template_id>/criteria/<criterion_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def edit_criterion(template_id, criterion_id):
    template = models.RubricTemplate.objects.get(id=template_id)
    criterion = next((c for c in template.criteria if str(c.id) == criterion_id), None)

    if not criterion:
        return redirect(url_for("admin.rubrics.criteria", template_id=template.id))

    form = forms.rubrics.RubricCriterionForm(obj=criterion)
    form.clos.choices = get_clo_choices(template.curriculums)

    if request.method == "GET":
        form.clos.data = [str(clo.id) for clo in criterion.clos]
        for level, field_name in forms.rubrics.LEVEL_FIELD_MAP:
            getattr(form, field_name).data = criterion.get_level_explanation(level)

    if not form.validate_on_submit():
        return render_template(
            "admin/rubrics/edit-criterion.html.j2",
            template=template,
            criterion=criterion,
            form=form,
        )

    clos = models.CLO.objects(id__in=form.clos.data)
    criterion.name = form.name.data
    criterion.description = form.description.data
    criterion.max_score = form.max_score.data
    criterion.clos = list(clos)

    level_explanations = []
    for level, field_name in forms.rubrics.LEVEL_FIELD_MAP:
        exp = getattr(form, field_name).data or ""
        level_explanations.append(
            models.RubricLevelExplanation(level=level, explanation=exp)
        )
    criterion.level_explanations = level_explanations

    template.save()

    return redirect(url_for("admin.rubrics.criteria", template_id=template.id))


@module.route("/<template_id>/criteria/<criterion_id>/remove")
@acl.roles_required("admin")
def remove_criterion(template_id, criterion_id):
    template = models.RubricTemplate.objects.get(id=template_id)
    if template.is_editable():
        template.criteria = [
            c for c in template.criteria if str(c.id) != criterion_id
        ]
        template.save()

    return redirect(url_for("admin.rubrics.criteria", template_id=template.id))


@module.route("/<template_id>/criteria/<criterion_id>/move/<direction>")
@acl.roles_required("admin")
def move_criterion(template_id, criterion_id, direction):
    template = models.RubricTemplate.objects.get(id=template_id)
    if template.is_editable():
        ordered = template.get_sorted_criteria()
        index = next(
            (i for i, c in enumerate(ordered) if str(c.id) == criterion_id), None
        )
        if index is not None:
            swap_with = index - 1 if direction == "up" else index + 1
            if 0 <= swap_with < len(ordered):
                ordered[index].order, ordered[swap_with].order = (
                    ordered[swap_with].order,
                    ordered[index].order,
                )
                template.save()

    return redirect(url_for("admin.rubrics.criteria", template_id=template.id))


@module.route("/<template_id>/activate")
@acl.roles_required("admin")
def activate(template_id):
    template = models.RubricTemplate.objects.get(id=template_id)
    if template.get_total_max_score() != 100:
        flash(
            f"Cannot activate rubric template. The sum of criteria max scores must be 100 (current total: {template.get_total_max_score()}).",
            "warning",
        )
        return redirect(url_for("admin.rubrics.criteria", template_id=template.id))

    template.activate()

    return redirect(url_for("admin.rubrics.index"))


@module.route("/<template_id>/archive")
@acl.roles_required("admin")
def archive(template_id):
    template = models.RubricTemplate.objects.get(id=template_id)
    template.archive()

    return redirect(url_for("admin.rubrics.index"))


@module.route("/<template_id>/clone")
@acl.roles_required("admin")
def clone(template_id):
    template = models.RubricTemplate.objects.get(id=template_id)
    cloned = template.clone(creator=current_user._get_current_object())

    return redirect(url_for("admin.rubrics.criteria", template_id=cloned.id))
