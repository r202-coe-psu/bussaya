import logging

from bussaya import web
from bussaya.notifications import run_deadline_reminders


def main():
    logging.basicConfig(level=logging.INFO)

    app = web.create_app()
    with app.app_context():
        run_deadline_reminders(app)
