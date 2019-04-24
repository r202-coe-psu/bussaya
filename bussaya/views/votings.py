from flask import Blueprint, render_template
from flask_login import login_required, current_user

import mongoengine as me

from .. import forms
from .. import models

import datetime
import collections

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




