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
import math

import mongoengine as me

from bussaya import models
from bussaya.web import forms, acl


module = Blueprint("organizations", __name__, url_prefix="/organizations")

ORGANIZATIONS_PER_PAGE = 20


@module.route("")
@acl.roles_required("admin")
def index():
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    if not page or page < 1:
        page = 1

    organizations = models.Organization.objects(status="active")
    if query:
        organizations = organizations.filter(
            me.Q(name__icontains=query)
            | me.Q(website__icontains=query)
            | me.Q(address__icontains=query)
            | me.Q(remark__icontains=query)
        )
    organizations = organizations.order_by("name")

    total = organizations.count()
    total_pages = max(1, math.ceil(total / ORGANIZATIONS_PER_PAGE))
    if page > total_pages:
        page = total_pages

    organizations_page = organizations.skip((page - 1) * ORGANIZATIONS_PER_PAGE).limit(
        ORGANIZATIONS_PER_PAGE
    )

    return render_template(
        "admin/organizations/index.html.j2",
        organizations=organizations_page,
        query=query,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@module.route("/create", methods=["GET", "POST"], defaults=dict(organization_id=None))
@module.route("/<organization_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def create_or_edit(organization_id):
    form = forms.organizations.OrganizationForm()

    organization = None

    if organization_id:
        organization = models.Organization.objects.get(id=organization_id)
        form = forms.organizations.OrganizationForm(obj=organization)

    if not form.validate_on_submit():
        return render_template(
            "admin/organizations/create-or-edit.html.j2",
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

    return render_template("admin/organizations/view.html.j2", organization=organization)


@module.route(
    "/<organization_id>/mentors/add",
    methods=["GET", "POST"],
    defaults=dict(mentor_id=None),
)
@module.route("/<organization_id>/mentors/<mentor_id>/edit", methods=["GET", "POST"])
@acl.roles_required("admin")
def add_or_edit_mentor(organization_id, mentor_id):
    organization = models.Organization.objects.get(id=organization_id)

    form = forms.organizations.MentorForm()
    mentor = None

    if mentor_id:
        mentor = models.Mentor.objects.get(id=mentor_id)
        form = forms.organizations.MentorForm(obj=mentor)

    if not form.validate_on_submit():
        return render_template(
            "admin/organizations/add-or-edit-mentor.html.j2",
            form=form,
            mentor=mentor,
            organization=organization,
        )

    if not mentor:
        mentor = models.Mentor()
        mentor.created_date = datetime.datetime.now()
        mentor.status = "active"
        mentor.adder = current_user._get_current_object()
        mentor.organization = organization

    form.populate_obj(mentor)
    mentor.updated_date = datetime.datetime.now()
    mentor.last_updated_by = current_user._get_current_object()
    mentor.save()

    return redirect(
        url_for("admin.organizations.view", organization_id=organization.id)
    )
