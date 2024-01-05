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

import datetime


from bussaya import models
from bussaya.web import forms, acl


module = Blueprint("organizations", __name__, url_prefix="/organizations")


@module.route("")
@acl.roles_required("admin")
def index():
    organizations = models.Organization.objects(status="active")

    return render_template(
        "admin/organizations/index.html", organizations=organizations
    )


@module.route("/create", methods=["GET", "POST"], defaults=dict(organization_id=None))
@module.route("/<organization_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(organization_id):
    form = forms.organizations.OrganizationForm()

    organization = None

    if organization_id:
        organization = models.Organization.objects(id=organization)
        form = forms.organizations.OrganizationForm(obj=organization)

    if not form.validate_on_submit():
        return render_template(
            "admin/organizations/create-or-edit.html",
            form=form,
            organization=organization,
        )

    if not organization:
        organization = models.Organization()
        organization.created_date = datetime.datetime.now()
        organization.status = "active"
        organization.creator = current_user._get_current_object()

    form.populate_obj(organization)
    organization.updated_date = datetime.datetime.now()
    organization.last_updated_by = current_user._get_current_object()
    organization.save()

    return redirect(
        url_for("admin.organizations.view", organization_id=organization.id)
    )


@module.route("/<organization_id>")
@acl.roles_required("admin")
def view(organization_id):
    organization = models.Organization.objects(
        id=organization_id, status="active"
    ).first()

    if not organization:
        return redirect(url_for("admin.organizations.index"))

    return render_template("admin/organizations/view.html", organization=organization)
