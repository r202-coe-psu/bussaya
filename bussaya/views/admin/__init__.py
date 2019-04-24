from flask import Blueprint

from bussaya import acl

module = Blueprint('admin', __name__, url_prefix='/admin')



@module.route('/')
@acl.allows.requires(acl.is_admin)
def index():
    return 'admin'
