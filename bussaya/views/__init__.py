from flask import redirect, url_for
from flask_login import current_user

import datetime

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

def add_date_url(url):
    now = datetime.datetime.now()
    return f'{url}?date={now.strftime("%Y%m%d")}'


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
    app.add_template_filter(add_date_url)
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
    return redirect(url_for('site.index'))


