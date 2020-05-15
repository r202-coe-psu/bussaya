from flask import Blueprint, render_template
from flask_login import login_required, current_user

from .. import models
from .. import forms

import datetime

module = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def index_admin():
    class_ = models.Class.objects().order_by('-id').first()
    advisees = models.Project.objects(
            advisor=current_user._get_current_object(),
            class_=class_)
    committees = models.Project.objects(
            committees=current_user._get_current_object(),
            class_=class_)

    return render_template('/dashboard/index-admin.html',
                           class_=class_,
                           advisees=advisees,
                           committees=committees)


def index_lecturer():
    class_ = models.Class.objects().order_by('-id').first()
    advisees = models.Project.objects(
            advisor=current_user._get_current_object(),
            class_=class_)
    committees = models.Project.objects(
            committees=current_user._get_current_object(),
            class_=class_)
    return render_template('/dashboard/index-lecturer.html',
                           class_=class_,
                           advisees=advisees,
                           committees=committees)


def index_student():
    projects = models.Project.objects(students=current_user._get_current_object())
    return render_template('/dashboard/index-student.html',
                           projects=projects)


def index_user():
    return render_template('/dashboard/index-user.html')


@module.route('')
@login_required
def index():
    user = current_user
    if 'admin' in user.roles:
        return index_admin()
    elif 'CoE-lecturer' in user.roles:
        return index_lecturer()
    elif 'student' in user.roles:
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
        if 'admin' in user.roles:
            return render_template('/dashboard/index-admin.html')
        elif 'CoE-lecturer' in user.roles:
            return render_template('/dashboard/index-lecturer.html')

        return render_template('/votings/timeout.html')

    voting = models.Voting.objects(user=user, election=election)

    if voting:
        if 'admin' in user.roles:
            return render_template('/dashboard/index-admin.html')
        elif 'CoE-lecturer' in user.roles:
            return render_template('/dashboard/index-lecturer.html')
        return index_user()

    projects = models.Project.objects(class_=election.class_)

    form = forms.votings.VotingForm()

    project_choices = [('', 'กรุณาเลือกโปรเจค')]
    project_choices.extend([
            (str(project.id), '{} ({})'.format(
                project.name, ', '.join(project.student_ids)))
            for project in projects])
    form.projects.choices = project_choices

    if not form.validate_on_submit():
        return render_template('/votings/vote.html',
                               form=form,
                               now=datetime.datetime.now(),
                               election=election)

    voting = models.Voting(user=current_user._get_current_object(),
                           election=election,
                           class_=election.class_,
                           raw_voting_projects=form.projects.data)
    for project_id in form.projects.data:
        project = models.Project.objects.get(id=project_id)
        if project:
            voting.projects.append(project)
    voting.save()

    return render_template('/votings/waiting-results.html')
