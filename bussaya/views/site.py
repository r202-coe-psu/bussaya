from flask import Blueprint, render_template
from .. import models

module = Blueprint('site', __name__)


@module.route('/')
def index():
    class_ = models.Class.objects().order_by('-id').first()
    projects = models.Project.objects(class_=class_, public__ne='private').order_by('-id')
    projects = [p for p in projects if p.is_advisor_approval()]
    return render_template(
            '/site/index.html',
            class_=class_,
            projects=projects)
