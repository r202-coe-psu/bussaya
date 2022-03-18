from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

import datetime
import collections

from .. import models, forms, acl

module = Blueprint("votings", __name__, url_prefix="/votings")
subviews = []


@module.route("/", methods=["GET"])
@acl.roles_required("admin")
def index():
    election = models.Election.objects().order_by("-id").first()

    votings = models.Voting.objects(election=election)
    std_votings = dict()
    lec_votings = dict()

    for v in votings:
        projects = std_votings
        if "CoE-lecturer" in v.user.roles or "CoE-staff" in v.user.roles:
            projects = lec_votings

        project = v.project
        if project not in projects:
            projects[project] = 0

        projects[project] += 1

    std_votings = list(std_votings.items())
    lec_votings = list(lec_votings.items())
    std_votings.sort(key=lambda v: v[1], reverse=True)
    lec_votings.sort(key=lambda v: v[1], reverse=True)
    print(std_votings)

    return render_template(
        "/votings/index.html",
        election=election,
        std_votings=std_votings,
        lec_votings=lec_votings,
    )


@module.route(
    "/elections/<election_id>/projects/<project_id>/vote", methods=["GET", "POST"]
)
@login_required
def vote(election_id, project_id):
    now = datetime.datetime.now()
    election = models.Election.objects.get(id=election_id)

    project = models.Project.objects.get(
        id=project_id,
        class_=election.class_,
    )

    if now < election.started_date or election.ended_date < now:
        message = f"ไม่อยู่ในช่วงเวลาลงโหวต"
        return render_template(
            "/votings/vote-fail.html",
            election=election,
            message=message,
            project=project,
        )

    voting = models.Voting.objects(
        user=current_user._get_current_object(),
        election=election,
        class_=election.class_,
        project=project,
    ).first()

    if voting:
        return redirect(
            url_for(
                "votings.vote_success",
                voting_id=voting.id,
            )
        )

    form = forms.votings.VotingForm()
    if not form.validate_on_submit():
        return render_template(
            "/votings/vote.html",
            project=project,
            election=election,
            form=form,
        )
    voting = models.Voting()
    voting.user = current_user._get_current_object()
    voting.remark = form.remark.data

    if form.location.data:
        voting.location = [
            float(f) for f in form.location.data.split(",") if len(f.strip()) > 0
        ]
    else:
        voting.location = [0, 0]

    voting.ip_address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr)
    voting.user_agent = request.environ.get("HTTP_USER_AGENT", "")
    voting.client = request.environ.get("HTTP_SEC_CH_UA", "")

    voting.election = election
    voting.project = project
    voting.class_ = project.class_

    data = form.data
    data.pop("csrf_token")
    voting.data = data

    voting.save()

    return redirect(
        url_for(
            "votings.vote_success",
            voting_id=voting.id,
        )
    )


@module.route("/<voting_id>/success")
@login_required
def vote_success(voting_id):
    voting = models.Voting.objects.get(
        id=voting_id,
        user=current_user._get_current_object(),
    )
    return render_template(
        "/votings/vote-success.html",
        voting=voting,
        project=voting.project,
        class_=voting.class_,
        election=voting.election,
    )
