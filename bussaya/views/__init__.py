from flask import redirect, url_for
from flask_login import current_user

from . import site
from . import accounts
from . import dashboard
from . import projects
from . import classes
from . import votings
from . import elections
from . import tags

from . import admin
# from . import administration


def get_subblueprints(views=[]):
    blueprints = []
    for view in views:
        blueprints.append(view.module)

        if 'subviews' in dir(view):
            for module in get_subblueprints(view.subviews):
                if view.module.url_prefix and module.url_prefix:
                    module.url_prefix = view.module.url_prefix + \
                            module.url_prefix
                blueprints.append(module)

    return blueprints


def register_blueprint(app):
    blueprints = get_subblueprints([site,
                                    dashboard,
                                    accounts,
                                    projects,
                                    classes,
                                    votings,
                                    elections,
                                    admin,
                                    tags
                                    ])

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    app.register_error_handler(403, page_forbidden)


def page_forbidden(e):

    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))

    return e
