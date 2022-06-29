from .users import User
from .oauth2 import OAuth2Token
from .classes import Class
from .groups import Group
from .projects import Project, ProjectResource, ProjectApproval
from .votings import Voting, Election
from .submissions import Submission, StudentWork, Meeting
from .grades import Grade, StudentGrade

from flask_mongoengine import MongoEngine

db = MongoEngine()

__all__ = [
    User,
    OAuth2Token,
    Class,
    Group,
    Project,
    ProjectResource,
    ProjectApproval,
    Voting,
    Election,
    Submission,
    StudentWork,
    Meeting,
    Grade,
    StudentGrade,
]


def init_db(app):
    db.init_app(app)


def init_mongoengine(settings):
    import mongoengine as me

    dbname = settings.get("MONGODB_DB")
    host = settings.get("MONGODB_HOST", "localhost")
    port = int(settings.get("MONGODB_PORT", "27017"))
    username = settings.get("MONGODB_USERNAME", "")
    password = settings.get("MONGODB_PASSWORD", "")

    me.connect(db=dbname, host=host, port=port, username=username, password=password)
