from flask import Blueprint, render_template
from flask_login import login_required, current_user

import datetime
import collections

from .. import models, forms

module = Blueprint('votings', __name__, url_prefix='/votings')
subviews = []


@module.route('/', methods=['GET'])
@login_required
def index():
    election = models.Election.objects().order_by('-id').first()

    votings = models.Voting.objects(election=election)
    std_votings = dict()
    lec_votings = dict()

    for v in votings:
        projects = std_votings
        if 'CoE-lecturer' in v.user.roles:
            projects = lec_votings

        for p in v.projects:
            if p not in projects:
                projects[p] = 1
            else:
                projects[p] += 1

    return render_template('/votings/index.html',
                           std_votings=collections.OrderedDict(std_votings),
                           lec_votings=collections.OrderedDict(lec_votings))


@module.route('/elections/<election_id>/projects/<project_id>/vote', methods=['GET'])
@login_required
def vote(election_id, project_id):
    now = datetime.datetime.now()
    election = models.Election.objects.get(id=election_id)

    if now < election.started_date or election.ended_date < now:
        message = f'ไม่อยู่ในช่วงเวลาลงเวลา'
        return render_template(
                '/activities/register_fail.html',
                activity=activity,
                message=message,
                )


    project = models.Project.objects.get(
            id=project_id,
            class_=election.class_,
            )
    
    voting = models.Voting.objects(
            user=current_user._get_current_object(),
            election=election,
            class_=election.class_,
            )

    if voting:
        return 'You are vote'

    form = forms.votings.VotingForm()
    if not form.validate_on_submit():
        return render_template('/votings/vote.html',
                               project=project,
                               election=election,
                               form=form,
                               )

    if form.student_id.data != current_user.username:
        message = f'รหัสนักศึกษา {form.student_id.data} ไม่ตรงกับบัญชีผู้ใช้'
        return render_template(
                '/activities/register_fail.html',
                activity=activity,
                message=message,
                )

    ap = models.ActivityParticipator()
    ap.user = current_user._get_current_object()
    ap.remark = form.remark.data
    ap.section = form.section.data
    ap.accepted = form.accepted.data
    ap.activity = activity
    if form.location.data:
        ap.location = [float(f) for f in form.location.data.split(',') if len(f.strip()) > 0]
    else:
        ap.location = [0, 0]

    ap.ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    ap.user_agent = request.environ.get('HTTP_USER_AGENT', '')
    ap.client = request.environ.get('HTTP_SEC_CH_UA', '')

    data = form.data
    data.pop('csrf_token')
    ap.data = data
    ap.save()

    return redirect(
            url_for(
                'activities.register_success',
                activity_id=activity.id,
                ))




    return 'Vote Done'


    

