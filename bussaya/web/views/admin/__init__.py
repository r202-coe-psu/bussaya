from flask import Blueprint, render_template

from bussaya import models
from bussaya.web import acl


module = Blueprint("admin", __name__, url_prefix="/admin")


@module.route("/")
@acl.roles_required("admin")
def index():
    menu = [
        {
            "label": "Classes",
            "description": "Create and manage classes, rounds, and student rosters.",
            "icon": "fa-solid fa-users",
            "endpoint": "admin.classes.index",
            "count": models.Class.objects.count(),
        },
        {
            "label": "Organizations",
            "description": "Cooperative-education organizations and mentors.",
            "icon": "fa-solid fa-building",
            "endpoint": "admin.organizations.index",
            "count": models.Organization.objects(status="active").count(),
        },
        {
            "label": "Curriculums",
            "description": "Curriculums, PLOs, and CLOs.",
            "icon": "fa-solid fa-book",
            "endpoint": "admin.curriculums.index",
            "count": models.Curriculum.objects(status="active").count(),
        },
        {
            "label": "Rubric Templates",
            "description": "Grading rubric templates and criteria.",
            "icon": "fa-solid fa-list-check",
            "endpoint": "admin.rubrics.index",
            "count": models.RubricTemplate.objects(status="active").count(),
        },
        {
            "label": "Email Templates",
            "description": "Deadline-reminder email subject and body text.",
            "icon": "fa-solid fa-envelope",
            "endpoint": "admin.email_templates.index",
            "count": models.EmailTemplate.objects.count(),
            "count_label": "customized",
        },
        {
            "label": "Users",
            "description": "Accounts, roles, and permissions.",
            "icon": "fa-solid fa-award",
            "endpoint": "admin.users.index",
            "count": models.User.objects.count(),
        },
        {
            "label": "Manage Election",
            "description": "Create and run project-award elections.",
            "icon": "fa-solid fa-check-to-slot",
            "endpoint": "elections.index",
            "count": models.Election.objects.count(),
        },
        {
            "label": "View Vote",
            "description": "Review submitted votes.",
            "icon": "fa-solid fa-square-poll-vertical",
            "endpoint": "votings.index",
            "count": models.Voting.objects.count(),
        },
    ]

    return render_template("/admin/index.html.j2", menu=menu)
