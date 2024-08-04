from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from bussaya import models
from .. import forms

import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@module.route("/admin")
@login_required
def index_admin():
    classes = models.Class.objects.all()
    opened_classes = []
    user = current_user._get_current_object()

    for class_ in classes:
        if class_.is_in_time():
            opened_classes.append(class_)

    return render_template(
        "/dashboard/index-admin.html",
        classes=classes,
        opened_classes=opened_classes,
    )


def index_lecturer():
    now = datetime.date.today()
    opened_classes = models.Class.objects(
        started_date__lte=now, ended_date__gte=now
    ).order_by("-id")
    classes = models.Class.objects.all()
    user = current_user._get_current_object()

    student_ids = []
    for oc in opened_classes:
        student_ids.extend(oc.student_ids)

    students = models.User.objects(username__in=student_ids)

    advisee_projects = models.Project.objects(
        advisors=current_user._get_current_object(),
        students__in=students,
        status="active",
    )
    committee_projects = models.Project.objects(
        committees=current_user._get_current_object(),
        students__in=students,
        status="active",
    )

    alumni_projects = models.Project.objects(
        advisors=current_user._get_current_object(),
        class___nin=opened_classes,
        status="active",
    ).order_by("-id")

    advisee_projects = sorted(
        advisee_projects,
        key=lambda p: (
            p.get_opened_class().type,
            [s.username for s in p.students],
        ),
    )

    committee_projects = sorted(
        committee_projects,
        key=lambda p: (
            p.get_opened_class().type,
            [advisor.username for advisor in p.advisors],
            [s.username for s in p.students],
        ),
    )

    return render_template(
        "/dashboard/index-lecturer.html",
        classes=classes,
        opened_classes=opened_classes,
        alumni_projects=alumni_projects,
        advisee_projects=advisee_projects,
        committee_projects=committee_projects,
    )


def index_student():
    projects = models.Project.objects(
        students=current_user._get_current_object(), status="active"
    )

    classes = models.Class.objects.all()
    available_class = []
    user = current_user._get_current_object()

    for class_ in classes:
        if class_.is_in_time() and user.username in class_.student_ids:
            available_class.append(class_)

    return render_template(
        "/dashboard/index-student.html",
        projects=projects,
        available_class=available_class,
    )


def index_user():
    return render_template("/dashboard/index-user.html")


@module.route("/")
@login_required
def index():
    user = current_user
    dev = request.args.get("dev")
    if dev == "test":
        return index_student()
    elif "CoE-lecturer" in user.roles or "lecturer" in user.roles:
        return index_lecturer()
    elif "student" in user.roles:
        return index_student()
    elif "admin" in user.roles:
        return redirect(url_for("dashboard.index_admin"))

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

    projects = models.Project.objects(class_=election.class_, status="active")

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
