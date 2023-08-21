from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
import mongoengine as me
import datetime

from bussaya import models

from .admin import round_grades as admin_round_grades
from .. import forms, acl

module = Blueprint("round_grades", __name__, url_prefix="/round_grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/round_grades/index.html", class_=class_)


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
        class_=class_, lecturer=user, round_grade=round_grade
    )

    student_grades = sorted(
        student_grades,
        key=lambda s: (
            [advisor.username for advisor in s.project.advisors],
            s.student.username,
        ),
    )

    return render_template(
        "/round_grades/view.html",
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
        round_grade=round_grade, lecturer=user
    )
    student_grades = sorted(
        student_grades,
        key=lambda s: (
            sorted([advisor.username for advisor in s.project.advisors]),
            s.student.username,
        ),
    )

    form = forms.round_grades.GroupGradingForm()
    for s in student_grades:
        form.gradings.append_entry(
            {"student_id": str(s.student.id), "result": s.result}
        )

    return render_template(
        "round_grades/grading.html",
        form=form,
        class_=class_,
        round_grade=round_grade,
        user=user,
        student_grades=student_grades,
    )


@module.route("/<round_grade_id>/submit_grade", methods=["GET", "POST"])
@acl.roles_required("lecturer")
def submit_grade(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
    user = current_user._get_current_object()

    if not round_grade.is_in_time():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade_id))

    form = forms.round_grades.GroupGradingForm()

    if not form.validate_on_submit():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade_id))

    for grading in form.gradings.data:
        student = models.User.objects.get(id=grading["student_id"])
        project = models.Project.objects(
            (me.Q(creator=student) | me.Q(students=student))
            & (me.Q(advisors=user) | me.Q(committees=user))
        ).first()

        if not project:
            continue

        student_grade = models.StudentGrade.objects(
            student=student,
            class_=class_,
            round_grade=round_grade,
            lecturer=user,
            # project=project,
        ).first()

        student_grade.result = grading["result"]
        student_grade.save()

        if (
            current_user._get_current_object() in project.advisors
            and grading["result"] != "-"
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


@module.route("/<class_id>/round_grades/view-total-round_grade")
@acl.roles_required("student")
def view_student_grades(class_id):
    student = current_user._get_current_object()
    class_ = models.Class.objects.get(id=class_id)

    project = student.get_project()

    round_grades = models.RoundGrade.objects(class_=class_)
    average_total_grade = student.get_complete_grade(class_)

    return render_template(
        "/round_grades/view-student.html",
        student=student,
        class_=class_,
        project=project,
        round_grades=round_grades,
        average_total_grade=average_total_grade,
    )
