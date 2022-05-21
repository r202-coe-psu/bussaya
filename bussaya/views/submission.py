from flask import Blueprint, render_template, redirect, url_for, send_file
from flask_login import login_required, current_user
from .. import forms
from .. import models
import mongoengine as me

import datetime

module = Blueprint("submission", __name__, url_prefix="/submission")


@module.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = forms.submissions.SubmissionForm()
    if not form.validate_on_submit():
        return render_template(
            "/submissions/add.html",
            form=form,
        )

    submission = models.Submission(
        user=current_user._get_current_object(),
    )

    form.populate_obj(submission)

    submission.save()

    return redirect(url_for("submission.index"))
