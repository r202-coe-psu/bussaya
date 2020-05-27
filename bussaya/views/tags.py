from flask import Blueprint, render_template
from .. import models
from .. import caches

module = Blueprint('tags', __name__, url_prefix='/tags')


@caches.cache.cached(timeout=3600)
@module.route('/')
def index():
    tags = models.Project.objects(public__ne='private').item_frequencies('tags', normalize=True)
    return render_template(
            '/tags/index.html',
            tags=tags)


@module.route('/<name>')
def view(name):
    projects = models.Project.objects(tags=name, public__ne='private').order_by('-id')
    return render_template(
            '/tags/view.html',
            name=name,
            projects=projects)
