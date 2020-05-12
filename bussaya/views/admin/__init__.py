from flask import Blueprint

from bussaya import acl

from . import classes
subviews = [classes]


module = Blueprint('admin', __name__, url_prefix='/admin')


@module.route('/')
@acl.admin_permission.require()
def index():
    return 'admin'
