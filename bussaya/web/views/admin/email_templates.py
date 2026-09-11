from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

from bussaya import models
from bussaya.web import forms, acl

module = Blueprint("email_templates", __name__, url_prefix="/email_templates")


@module.route("")
@acl.roles_required("admin")
def index():
    templates = [
        {
            "type": type_key,
            "label": type_label,
            "template": models.EmailTemplate.objects(type=type_key).first(),
        }
        for type_key, type_label in models.EMAIL_TEMPLATE_TYPE
    ]

    return render_template("admin/email_templates/index.html.j2", templates=templates)


@module.route("/<template_type>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def edit(template_type):
    if template_type not in dict(models.EMAIL_TEMPLATE_TYPE):
        return redirect(url_for("admin.email_templates.index"))

    template = models.EmailTemplate.get_or_create_default(template_type)

    form = forms.email_templates.EmailTemplateForm(obj=template)

    if not form.validate_on_submit():
        return render_template(
            "admin/email_templates/edit.html.j2", form=form, template=template
        )

    form.populate_obj(template)
    template.last_updated_by = current_user._get_current_object()
    template.save()

    return redirect(url_for("admin.email_templates.index"))
