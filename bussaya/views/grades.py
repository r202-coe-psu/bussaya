from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl

module = Blueprint("grades", __name__, url_prefix="/grades")


@module.route("/<class_id>")
@login_required
@acl.roles_required("admin", "lecturer")
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    grade = models.Grade(class_=class_)

    return render_template("/grades/index.html", class_=class_)
