import math

from flask import Blueprint, render_template, request

from bussaya import models
from bussaya.web import acl

module = Blueprint("email_logs", __name__, url_prefix="/email_logs")

LOGS_PER_PAGE = 30

TARGET_MODELS = {
    "round_grade": models.RoundGrade,
    "meeting": models.Meeting,
    "report": models.Submission,
    "presentation": models.Submission,
}


def _describe_target(log):
    model = TARGET_MODELS.get(log.target_type)
    target = model.objects(id=log.target_id).first() if model else None
    if not target:
        return "(deleted)"

    if log.target_type == "meeting":
        return f"{target.class_.name} - {target.name}"

    return f"{target.class_.name} - {target.get_type_display()}"


@module.route("/")
@acl.roles_required("admin")
def index():
    target_type = request.args.get("target_type", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    if not page or page < 1:
        page = 1

    logs = models.DeadlineNotification.objects.all()
    if target_type:
        logs = logs.filter(target_type=target_type)
    if status:
        logs = logs.filter(status=status)
    logs = logs.order_by("-sent_date")

    total = logs.count()
    total_pages = max(1, math.ceil(total / LOGS_PER_PAGE))
    if page > total_pages:
        page = total_pages

    logs_page = logs.skip((page - 1) * LOGS_PER_PAGE).limit(LOGS_PER_PAGE)
    rows = [{"log": log, "target_description": _describe_target(log)} for log in logs_page]

    return render_template(
        "/admin/email_logs/index.html.j2",
        rows=rows,
        target_type=target_type,
        status=status,
        page=page,
        total_pages=total_pages,
        total=total,
        target_types=models.notifications.DEADLINE_TARGET_TYPE,
    )
