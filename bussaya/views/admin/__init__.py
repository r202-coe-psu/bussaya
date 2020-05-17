from flask import Blueprint, render_template, redirect

from bussaya import acl, models

from . import classes
subviews = [classes]


module = Blueprint('admin', __name__, url_prefix='/admin')


@module.route('/')
@acl.admin_permission.require(http_exception=403)
def index():
    class_ = models.Class.objects().order_by('-id').first()

    if class_ is None:
        return redirect('dashboard.index')

    projects = models.Project.objects(class_=class_)

    return render_template('/admin/index.html',
                           class_=class_,
                           projects=projects)
