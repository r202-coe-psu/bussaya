from flask import Blueprint, render_template
from flask_login import login_required, current_user

from .. import models
import mongoengine as me

from .. import forms

import datetime

module = Blueprint('dashboard', __name__, url_prefix='/dashboard')
subviews = []



def index_admin():
    return render_template('/dashboard/index-admin.html')

def index_user():
    return render_template('/votings/waiting-results.html')

    # user = current_user
    # now = datetime.datetime.now()

    # available_classes = models.Class.objects(
    #         (me.Q(limited_enrollment__grantees=user.email) | 
    #              me.Q(limited_enrollment__grantees=user.username)) &
    #         (me.Q(started_date__lte=now) &
    #              me.Q(ended_date__gte=now))
    #         ).order_by('ended_date')


    # ass_schedule = []
    # for class_ in available_classes:
    #     if not class_.is_enrolled(user.id):
    #         continue

    #     for ass_t in class_.assignment_schedule:
    #         if ass_t.started_date <= now and now < ass_t.ended_date:
    #             ass_schedule.append(
    #                     dict(assignment_schedule=ass_t,
    #                          class_=class_))

    # def order_by_ended_date(e):
    #     return e['assignment_schedule'].ended_date

    # ass_schedule.sort(key=order_by_ended_date)

    # return render_template('/dashboard/index.html',
    #                        available_classes=available_classes,
    #                        assignment_schedule=ass_schedule
    #                        )

@module.route('/', methods=['GET', 'POST'])
@login_required
def index():
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
            (str(project.id),
             '{} ({})'.format(project.name,', '.join(project.student_ids))) \
            for project in projects])
    form.projects.choices = project_choices

    if not form.validate_on_submit():
        return render_template('/votings/vote.html',
                               form=form,
                               now = datetime.datetime.now(),
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
