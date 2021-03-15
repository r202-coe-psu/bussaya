from flask import Blueprint, render_template, redirect, url_for
import datetime

from .. import models
from .. import caches

module = Blueprint('site', __name__)


@module.route('/')
@caches.cache.cached(timeout=600)
def index():
    now = datetime.datetime.now()
    election = models.Election.objects(
            started_date__lte=now,
            ended_date__gte=now,
            ).first()
    if election:
        return redirect(
                url_for(
                    'elections.show_election',
                    election_id=election.id))

    classes = models.Class.objects(ended_date__lt=now)
    projects = models.Project.objects(
            public__ne='private',class___in=classes).order_by('-id').limit(100)
    return render_template(
            '/site/index.html',
            projects=projects)
