from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from .. import models
from .. import forms

import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def get_current_class():
    class_ = models.Class.objects().order_by("-id").first()
    advisees = models.Project.objects(
        advisor=current_user._get_current_object(), class_=class_
    )
    committees = models.Project.objects(
        committees=current_user._get_current_object(), class_=class_
    )

    alumni_projects = models.Project.objects(
        advisor=current_user._get_current_object(),
        class___ne=class_,
    )
    data = dict(
        class_=class_,
        advisees=advisees,
        committees=committees,
        alumni_projects=alumni_projects,
    )
    return data


def index_admin():
    data = get_current_class()
    return render_template("/dashboard/index-admin.html", **data)


def index_lecturer():
    class_, advisees, committees = get_current_class()
    return render_template("/dashboard/index-lecturer.html", **data)


def index_student():
    projects = models.Project.objects(students=current_user._get_current_object())

    classes = models.Class.objects.all()
    available_class = []

    for class_ in classes:
        if class_.in_time():
            available_class.append(class_)

    return render_template(
        "/dashboard/index-student.html",
        projects=projects,
        available_class=available_class,
    )


def index_user():
    return render_template("/dashboard/index-user.html")


@module.route("")
@login_required
def index():
    user = current_user
    dev = request.args.get("dev")
    if dev == "test":
        return index_student()
    if "admin" in user.roles:
        return index_admin()
    elif "CoE-lecturer" in user.roles:
        return index_lecturer()
    elif "student" in user.roles:
        return index_student()

    return index_user()


def index_voting():
    now = datetime.datetime.now()
    user = current_user._get_current_object()
    election = models.Election.objects(
        started_date__lte=now,
        ended_date__gte=now,
    ).first()

    if not election:
        if "admin" in user.roles:
            return render_template("/dashboard/index-admin.html")
        elif "CoE-lecturer" in user.roles:
            return render_template("/dashboard/index-lecturer.html")

        return render_template("/votings/timeout.html")

    voting = models.Voting.objects(user=user, election=election)

    if voting:
        if "admin" in user.roles:
            return render_template("/dashboard/index-admin.html")
        elif "CoE-lecturer" in user.roles:
            return render_template("/dashboard/index-lecturer.html")
        return index_user()

    projects = models.Project.objects(class_=election.class_)

    form = forms.votings.VotingForm()

    project_choices = [("", "กรุณาเลือกโปรเจค")]
    project_choices.extend(
        [
            (
                str(project.id),
                "{} ({})".format(project.name, ", ".join(project.student_ids)),
            )
            for project in projects
        ]
    )
    form.projects.choices = project_choices

    if not form.validate_on_submit():
        return render_template(
            "/votings/vote.html",
            form=form,
            now=datetime.datetime.now(),
            election=election,
        )

    voting = models.Voting(
        user=current_user._get_current_object(),
        election=election,
        class_=election.class_,
        raw_voting_projects=form.projects.data,
    )
    for project_id in form.projects.data:
        project = models.Project.objects.get(id=project_id)
        if project:
            voting.projects.append(project)
    voting.save()

    return render_template("/votings/waiting-results.html")
