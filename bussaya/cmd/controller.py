import logging

from bussaya import models
from bussaya.config import load_settings
from bussaya.controller import run_deadline_reminders


def main():
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    models.init_mongoengine(settings)
    run_deadline_reminders(settings)
