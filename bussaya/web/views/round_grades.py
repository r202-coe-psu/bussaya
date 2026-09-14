from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    request,
    jsonify,
)
from flask_login import login_required, current_user
import mongoengine as me
import datetime

from bussaya import models
from bussaya.models import rubrics as rubric_models

from .admin import round_grades as admin_round_grades
from .. import forms, acl

module = Blueprint("round_grades", __name__, url_prefix="/round_grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/round_grades/index.html.j2", class_=class_)


@module.route("/<round_grade_type>/view")
@acl.roles_required("lecturer")
def view(round_grade_type):
    class_id = request.args.get("class_id", None)
    if not class_id:
        return redirect(url_for("dashboard.index"))

    class_ = models.Class.objects.get(id=class_id)
    user = current_user._get_current_object()
    round_grade = models.RoundGrade.objects(
        type=round_grade_type, class_=class_
    ).first()

    if not round_grade:
        return redirect(url_for("classes.view", class_id=class_.id))

    if round_grade.is_in_time():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade.id))

    student_grades = models.StudentGrade.objects(
        class_=class_, grader__lecturer=user, round_grade=round_grade
    )

    student_grades = sorted(
        student_grades,
        key=lambda s: (
            [
                advisor.username
                for advisor in s.project.advisors
                if s.project.status == "active"
            ],
            s.student.username,
        ),
    )

    round_grade_rubric = rubric_models.get_or_create_round_grade_rubric(round_grade)

    return render_template(
        "/round_grades/view.html.j2",
        user=user,
        class_=class_,
        round_grade=round_grade,
        round_grade_rubric=round_grade_rubric,
        final_grade_scale=admin_round_grades.get_final_grade_scale(user),
        round_grade_type=round_grade_type,
        student_grades=student_grades,
    )


@module.route("/<round_grade_type>/approve_report")
@acl.roles_required("lecturer")
def approve_report(round_grade_type):
    class_id = request.args.get("class_id", None)
    if not class_id:
        return redirect(url_for("dashboard.index"))

    class_ = models.Class.objects.get(id=class_id)
    user = current_user._get_current_object()
    round_grade = models.RoundGrade.objects(
        type=round_grade_type, class_=class_
    ).first()

    if not round_grade:
        return redirect(url_for("classes.view", class_id=class_.id))

    if round_grade.is_in_time():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade.id))

    student_grades = models.StudentGrade.objects(
        class_=class_, grader__lecturer=user, round_grade=round_grade
    )

    student_grades = sorted(
        student_grades,
        key=lambda s: (
            [advisor.username for advisor in s.project.advisors],
            s.student.username,
        ),
    )

    return render_template(
        "/round_grades/approve-report.html.j2",
        user=user,
        class_=class_,
        round_grade=round_grade,
        round_grade_type=round_grade_type,
        student_grades=student_grades,
    )


@module.route("/<round_grade_id>/grading", methods=["GET", "POST"])
@acl.roles_required("lecturer")
def grading(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
    if not round_grade.is_in_time():
        return redirect(
            url_for(
                "round_grade.view",
                class_id=class_.id,
                round_grade_type=round_grade.type,
            )
        )
    user = current_user._get_current_object()
    admin_round_grades.check_and_create_student_grade_profile(round_grade, user)

    student_grades = models.StudentGrade.objects.all().filter(
        round_grade=round_grade, grader__lecturer=user
    )
    student_grades = sorted(
        student_grades,
        key=lambda s: (
            sorted([advisor.username for advisor in s.project.advisors]),
            s.project.name,
            s.student.username,
        ),
    )

    round_grade_rubric = rubric_models.get_or_create_round_grade_rubric(round_grade)
    form = (
        admin_round_grades.build_rubric_grading_form(
            forms.round_grades.GroupRubricGradingForm,
            student_grades,
            round_grade_rubric,
        )
        if round_grade_rubric
        else forms.round_grades.GroupRubricGradingForm()
    )

    return render_template(
        "round_grades/grading.html.j2",
        form=form,
        class_=class_,
        round_grade=round_grade,
        round_grade_rubric=round_grade_rubric,
        user=user,
        student_grades=student_grades,
        final_grade_scale=admin_round_grades.get_final_grade_scale(user),
    )


@module.route("/<round_grade_id>/submit_grade", methods=["GET", "POST"])
@acl.roles_required("lecturer")
def submit_grade(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
    user = current_user._get_current_object()

    if not round_grade.is_in_time():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade_id))

    round_grade_rubric = rubric_models.get_or_create_round_grade_rubric(round_grade)
    form = forms.round_grades.GroupRubricGradingForm()

    if not round_grade_rubric or not form.validate_on_submit():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade_id))

    for grading in form.gradings.data:
        student = models.User.objects.get(id=grading["student_id"])
        project = models.Project.objects(
            (me.Q(creator=student) | me.Q(students=student))
            & (me.Q(advisors=user) | me.Q(committees=user)),
            status="active",
        ).first()

        if not project:
            continue

        student_grade = models.StudentGrade.objects(
            student=student,
            class_=class_,
            round_grade=round_grade,
            grader__lecturer=user,
            # project=project,
        ).first()

        if not student_grade:
            continue

        admin_round_grades.save_rubric_score(
            student_grade, round_grade_rubric, grading["criterion_scores"]
        )
        student_grade.updated_date = datetime.datetime.now()
        student_grade.save()

        if (
            current_user._get_current_object() in project.advisors
            and student_grade.result != "-"
        ):
            meetings = models.MeetingReport.objects(
                class_=class_, owner=student_grade.student, status__in=[None, "wait"]
            )
            for meeting in meetings:
                meeting.status = "approved"
                meeting.approver = current_user._get_current_object()
                meeting.approved_date = datetime.datetime.now()
                meeting.approver_ip_address = request.headers.get(
                    "X-Forwarded-For", request.remote_addr
                )
                meeting.save()

    return redirect(
        url_for(
            "round_grades.view",
            class_id=class_.id,
            round_grade_type=round_grade.type,
        )
    )


@module.route("/<round_grade_id>/submit_grade_one", methods=["POST"])
@acl.roles_required("lecturer")
def submit_grade_one(round_grade_id):
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError

    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
    user = current_user._get_current_object()

    if not round_grade.is_in_time():
        return jsonify({"ok": False, "error": "Grading window is closed."}), 400

    payload = request.get_json(silent=True) or {}

    try:
        validate_csrf(payload.get("csrf_token"))
    except ValidationError:
        return jsonify({"ok": False, "error": "Invalid CSRF token."}), 400

    round_grade_rubric = rubric_models.get_or_create_round_grade_rubric(round_grade)
    if not round_grade_rubric:
        return jsonify({"ok": False, "error": "No active rubric."}), 400

    student = models.User.objects(id=payload.get("student_id")).first()
    if not student:
        return jsonify({"ok": False, "error": "Student not found."}), 404

    student_grade = models.StudentGrade.objects(
        student=student,
        class_=class_,
        round_grade=round_grade,
        grader__lecturer=user,
    ).first()
    if not student_grade:
        return jsonify({"ok": False, "error": "Grading record not found."}), 404

    criterion_scores_data = []
    for entry in payload.get("criterion_scores", []):
        score = entry.get("score")
        try:
            score = float(score) if score not in (None, "") else None
        except (TypeError, ValueError):
            score = None
        criterion_scores_data.append(
            {"criterion_id": entry.get("criterion_id"), "score": score}
        )

    admin_round_grades.save_rubric_score(
        student_grade, round_grade_rubric, criterion_scores_data
    )
    student_grade.updated_date = datetime.datetime.now()
    student_grade.save()

    project = models.Project.objects(
        (me.Q(creator=student) | me.Q(students=student))
        & (me.Q(advisors=user) | me.Q(committees=user)),
        status="active",
    ).first()

    if project and user in project.advisors and student_grade.result != "-":
        meetings = models.MeetingReport.objects(
            class_=class_, owner=student, status__in=[None, "wait"]
        )
        for meeting in meetings:
            meeting.status = "approved"
            meeting.approver = user
            meeting.approved_date = datetime.datetime.now()
            meeting.approver_ip_address = request.headers.get(
                "X-Forwarded-For", request.remote_addr
            )
            meeting.save()

    scored = sum(1 for c in criterion_scores_data if c["score"] is not None)
    actual_grade, caused = student.get_actual_grade(student_grade.round_grade)

    return jsonify(
        {
            "ok": True,
            "scored": scored,
            "total": len(criterion_scores_data),
            "result_display": student_grade.get_result_display(),
            "average_grade": student.get_average_grade(student_grade.round_grade),
            "actual_grade": actual_grade,
            "caused": caused or [],
        }
    )


@module.route("/<class_id>/round_grades/view-total-round_grade")
@acl.roles_required("student")
def view_student_grades(class_id):
    student = current_user._get_current_object()
    class_ = models.Class.objects.get(id=class_id)

    project = student.get_project()

    round_grades = models.RoundGrade.objects(class_=class_)
    average_total_grade = student.get_complete_grade(class_)

    return render_template(
        "/round_grades/view-student.html.j2",
        student=student,
        class_=class_,
        project=project,
        round_grades=round_grades,
        average_total_grade=average_total_grade,
    )
