from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required

import mongoengine as me

from bussaya import models
from bussaya.web import acl, forms

import datetime
import math

module = Blueprint("users", __name__, url_prefix="/users")

USERS_PER_PAGE = 20


@module.route("/")
@acl.roles_required("admin")
def index():
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    if not page or page < 1:
        page = 1

    users = models.User.objects.all()
    if query:
        users = users.filter(
            me.Q(first_name__icontains=query)
            | me.Q(last_name__icontains=query)
            | me.Q(first_name_th__icontains=query)
            | me.Q(last_name_th__icontains=query)
            | me.Q(username__icontains=query)
            | me.Q(email__icontains=query)
        )
    users = users.order_by("-username")

    total = users.count()
    total_pages = max(1, math.ceil(total / USERS_PER_PAGE))
    if page > total_pages:
        page = total_pages

    users_page = users.skip((page - 1) * USERS_PER_PAGE).limit(USERS_PER_PAGE)

    return render_template(
        "/admin/users/index.html.j2",
        users=users_page,
        query=query,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@module.route("/<user_id>", methods=["GET", "POST"])
@acl.roles_required("admin")
def view(user_id):
    user = models.User.objects.get(id=user_id)
    form = forms.accounts.AdminForm(
        obj=user,
    )
    if not form.validate_on_submit():
        return render_template("/admin/users/view.html.j2", form=form, user=user)

    form.populate_obj(user)

    user.updated_date = datetime.datetime.now()
    user.save()

    return redirect(url_for("admin.users.view", user_id=user.id))
