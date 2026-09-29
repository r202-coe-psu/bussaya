import logging

from bussaya import models
from bussaya.config import load_settings
from bussaya.controller import Server


def main():
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    server = Server(settings)
    server.start()
