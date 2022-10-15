from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user

import mongoengine as me

from bussaya import models
from bussaya.web import forms, acl

module = Blueprint("round_grades", __name__, url_prefix="/round_grades")


def get_lecturers_project_of_student(student):
    lecturers = []
    if not student:
        return lecturers
    project = student.get_project()
    if project:
        lecturers.append(project.advisor)
        for committee in project.committees:
            lecturers.append(committee)

    return lecturers


def create_student_grade(round_grade, student, lecturer):
    student_grade = models.StudentGrade(
        class_=round_grade.class_,
        round_grade=round_grade,
        student=student,
        lecturer=lecturer,
    )

    project = student.get_project()
    if project:
        student_grade.project = project

    student_grade.save()


def create_student_grade_profile(round_grade):

    # Project create after round_grade has been created.
    class_ = round_grade.class_
    for student in models.User.objects(username__in=class_.student_ids):
        for lecturer in get_lecturers_project_of_student(student):
            if not models.StudentGrade.objects(
                class_=class_,
                student=student,
                lecturer=lecturer,
                round_grade=round_grade,
            ):
                create_student_grade(class_, round_grade, student, lecturer)


def get_grading_student(class_, lecturer):
    students = models.User.objects(username__in=class_.student_ids)
    projects = models.Project.objects(
        (me.Q(creator__in=students) | me.Q(students__in=students))
        & (me.Q(advisor=lecturer) | me.Q(committees=lecturer))
    )
    grading_students = []
    for p in projects:
        if p.creator not in grading_students:
            grading_students.append(p.creator)

        for s in p.students:
            if s not in grading_students:
                grading_students.append(s)

    return grading_students


def check_and_crate_student_grade_profile(round_grade, lecturer):
    for student in get_grading_student(round_grade.class_, lecturer):
        if not models.StudentGrade.objects(
            class_=round_grade.class_,
            student=student,
            lecturer=lecturer,
            round_grade=round_grade,
        ).first():
            admin_round_grades.create_student_grade(round_grade, student, lecturer)


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/round_grades/index.html", class_=class_)


@module.route("/<round_grade_type>/view")
@acl.roles_required("admin")
def view(round_grade_type):
    class_id = request.args.get("class_id", None)
    if not class_id:
        return redirect(url_for("dashboard.index"))

    class_ = models.Class.objects.get(id=class_id)
    round_grade = models.RoundGrade.objects(
        type=round_grade_type, class_=class_
    ).first()
    if not round_grade:
        round_grade = models.RoundGrade(type=round_grade_type, class_=class_)
        round_grade.save()

    if round_grade.is_in_time():
        return redirect(
            url_for("admin.round_grades.grading", round_grade_id=round_grade.id)
        )

    student_grades = models.StudentGrade.objects(
        class_=class_,
        lecturer=current_user._get_current_object(),
        round_grade=round_grade,
    )
    student_grades = sorted(student_grades, key=lambda s: s.student.username)

    return render_template(
        "/admin/round_grades/view.html",
        user=current_user,
        class_=class_,
        round_grade=round_grade,
        round_grade_type=round_grade_type,
        student_grades=student_grades,
    )


@module.route("/<round_grade_type>/view_total")
@acl.roles_required("admin")
def view_total(round_grade_type):
    class_id = request.args.get("class_id", None)
    if not class_id:
        return redirect(url_for("dashboard.index"))

    class_ = models.Class.objects.get(id=class_id)
    user = current_user._get_current_object()

    round_grade = models.RoundGrade.objects.get(type=round_grade_type, class_=class_)
    total_student_grades = models.StudentGrade.objects(
        class_=class_, round_grade=round_grade
    )

    total_student_grades = sorted(
        total_student_grades, key=lambda s: s.student.username
    )

    student_grades = []
    if total_student_grades:
        student_grades = [total_student_grades[0]]
        for student_grade in total_student_grades:
            if student_grades[-1].student.username != student_grade.student.username:
                student_grades.append(student_grade)

    return render_template(
        "/admin/round_grades/view-total.html",
        user=user,
        class_=class_,
        round_grade=round_grade,
        round_grade_type=round_grade_type,
        student_grades=student_grades,
    )


def count_lecturer_given_grade(lecturer_grades):
    given_grade = 0
    for grade in lecturer_grades:
        if grade.result != "-":
            given_grade += 1

    return given_grade


@module.route("/<round_grade_type>/view_advisor")
@acl.roles_required("admin")
def view_advisor_grade(round_grade_type):
    class_id = request.args.get("class_id", None)
    if not class_id:
        return redirect(url_for("dashboard.index"))

    class_ = models.Class.objects.get(id=class_id)
    user = current_user._get_current_object()

    round_grade = models.RoundGrade.objects.get(type=round_grade_type, class_=class_)
    total_student_grades = models.StudentGrade.objects(
        class_=class_, round_grade=round_grade
    )
    lecturers = set([s.lecturer for s in total_student_grades])
    lecturers = sorted(lecturers, key=lambda l: l.first_name)

    print([lec.first_name for lec in lecturers])

    total_student_grades = sorted(
        total_student_grades, key=lambda s: s.student.username
    )

    student_grades = []
    if total_student_grades:
        student_grades = [total_student_grades[0]]
        for student_grade in total_student_grades:
            if student_grades[-1].student.username != student_grade.student.username:
                student_grades.append(student_grade)

    return render_template(
        "/admin/round_grades/view-advisor-grade.html",
        user=user,
        class_=class_,
        round_grade=round_grade,
        round_grade_type=round_grade_type,
        count_lecturer_given_grade=count_lecturer_given_grade,
        student_grades=student_grades,
        lecturers=lecturers,
    )


@module.route("/<round_grade_id>/grading", methods=["GET", "POST"])
@acl.roles_required("admin")
def grading(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
    if not round_grade.is_in_time():
        return redirect(
            url_for(
                "admin.round_grades.view",
                class_id=class_.id,
                round_grade_type=round_grade.type,
            )
        )

    user = current_user._get_current_object()
    check_and_crate_student_grade_profile(round_grade, user)
    student_grades = models.StudentGrade.objects.all().filter(
        round_grade=round_grade, lecturer=user
    )
    student_grades = sorted(student_grades, key=lambda s: s.student.username)

    form = forms.round_grades.GroupGradingForm()
    for s in student_grades:
        form.gradings.append_entry(
            {"student_id": str(s.student.id), "result": s.result}
        )

    return render_template(
        "/admin/round_grades/grading.html",
        form=form,
        class_=class_,
        round_grade=round_grade,
        user=user,
        student_grades=student_grades,
    )


@module.route("/<round_grade_id>/submit_grade", methods=["GET", "POST"])
@acl.roles_required("admin")
def submit_grade(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
    user = current_user._get_current_object()
    # student_grades = models.StudentGrade.objects(round_grade=round_grade, lecturer=user)

    form = forms.round_grades.GroupGradingForm()
    if not form.validate_on_submit():
        return redirect(
            url_for("admin.round_grades.grading", round_grade_id=round_grade_id)
        )

    for grading in form.gradings.data:
        print("grading", grading)
        student = models.User.objects.get(id=grading["student_id"])
        student_grade = models.StudentGrade.objects(
            student=student, class_=class_, round_grade=round_grade, lecturer=user
        ).first()

        student_grade.result = grading["result"]

        student_grade.save()

        if grading["result"] != "-":

            meetings = models.MeetingReport.objects(
                class_=class_, owner=student_grade.student, status=None
            )
            for meeting in meetings:
                meeting.status = "approved"
                meeting.approver = current_user._get_current_object()
                meeting.approver_ip_address = request.headers.get(
                    "X-Forwarded-For", request.remote_addr
                )
                meeting.remark += "\n\n-> approve by admin"
                meeting.save()

    return redirect(
        url_for(
            "admin.round_grades.view",
            class_id=class_.id,
            round_grade_type=round_grade.type,
        )
    )


@module.route("/<round_grade_id>/set_time", methods=["GET", "POST"])
@acl.roles_required("admin")
def set_time(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    round_grade_type = round_grade.type
    class_ = round_grade.class_
    form = forms.round_grades.RoundGradeForm(obj=round_grade)

    if not form.validate_on_submit():
        return render_template(
            "admin/round_grades/set-time.html",
            form=form,
            class_=class_,
            round_grade=round_grade,
            round_grade_type=round_grade.type,
        )

    form.populate_obj(round_grade)
    round_grade.save()

    create_student_grade_profile(round_grade)

    return redirect(
        url_for(
            "admin.round_grades.view",
            round_grade_type=round_grade.type,
            class_id=class_.id,
        )
    )


@module.route("/<round_grade_id>/release", methods=["GET", "POST"])
@acl.roles_required("admin")
def change_release_status(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    round_grade.release_status = (
        "released" if round_grade.release_status == "unreleased" else "unreleased"
    )

    round_grade.save()

    return redirect(
        url_for(
            "admin.round_grades.view",
            round_grade_type=round_grade.type,
            class_id=round_grade.class_.id,
        )
    )
