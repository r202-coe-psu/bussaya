from flask import Blueprint, render_template
from .. import models
from .. import caches

module = Blueprint('site', __name__)


@module.route('/')
@caches.cache.cached(timeout=600)
def index():
    projects = models.Project.objects(public__ne='private').order_by('-id').limit(150)
    return render_template(
            '/site/index.html',
            projects=projects)
