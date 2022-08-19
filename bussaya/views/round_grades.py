from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl
import mongoengine as me

module = Blueprint("round_grades", __name__, url_prefix="/round_grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/round_grades/index.html", class_=class_)


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


def create_student_grade(class_, round_grade, student, lecturer):
    student_grade = models.StudentGrade()
    student_grade.class_ = class_
    student_grade.round_grade = round_grade
    student_grade.student = student
    student_grade.lecturer = lecturer

    project = student.get_project()
    if project:
        student_grade.project = project

    student_grade.save()

    round_grade.save()


@module.route("/<round_grade_type>/view")
@acl.roles_required("lecturer")
def view(round_grade_type):
    class_id = request.args.get("class_id", None)
    if not class_id:
        return redirect(url_for("dashboard.index"))

    class_ = models.Class.objects.get(id=class_id)
    round_grades = models.RoundGrade.objects.all().filter(class_=class_)
    user = current_user._get_current_object()
    # Create Midterm and Final Grade
    if not round_grades:
        midterm = models.RoundGrade()
        midterm.type = "midterm"
        midterm.class_ = class_
        midterm.save()

        final = models.RoundGrade()
        final.type = "final"
        final.class_ = class_
        final.save()

        midterm.save()
        final.save()

    midterm = models.RoundGrade.objects.get(type="midterm", class_=class_)
    final = models.RoundGrade.objects.get(type="final", class_=class_)

    # Project create after round_grade has been created.

    for student in models.User.objects(username__in=class_.student_ids):
        for lecturer in get_lecturers_project_of_student(student):
            if not models.StudentGrade.objects(
                class_=class_, student=student, lecturer=lecturer, round_grade=midterm
            ):

                create_student_grade(class_, midterm, student, lecturer)
            if not models.StudentGrade.objects(
                class_=class_, student=student, lecturer=lecturer, round_grade=final
            ):
                create_student_grade(class_, final, student, lecturer)

    midterm.save()
    final.save()

    round_grade = models.RoundGrade.objects.get(type=round_grade_type, class_=class_)
    if round_grade.is_in_time():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade.id))

    student_grades = models.StudentGrade.objects(
        class_=class_, lecturer=user, round_grade=round_grade
    )

    student_grades = sorted(student_grades, key=lambda s: s.student.username)

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
            & (me.Q(advisor=user) | me.Q(committees=user))
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
            project.advisor == current_user._get_current_object()
            and grading["result"] != "-"
        ):
            meetings = models.MeetingReport.objects(
                class_=class_, owner=student_grade.student, status=None
            )
            for meeting in meetings:
                meeting.status = "approved"
                meeting.approver = current_user._get_current_object()
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
    round_grades = models.RoundGrade.objects.all().filter(class_=class_)

    total_grade = 0
    average_total_grade = 0
    for round_grade in round_grades:
        average_grade = student.get_average_grade(round_grade).lower()
        if round_grade.type == "midterm":
            grade_ratio = 0.4
        if round_grade.type == "final":
            grade_ratio = 0.6

        if average_grade == "incomplete" or round_grade.release_status == "unreleased":
            average_total_grade = "Incomplete"
            break

        if average_grade == "a":
            total_grade += grade_ratio * 4
        elif average_grade == "b+":
            total_grade += grade_ratio * 3.5
        elif average_grade == "b":
            total_grade += grade_ratio * 3
        elif average_grade == "c+":
            total_grade += grade_ratio * 2.5
        elif average_grade == "c":
            total_grade += grade_ratio * 2
        elif average_grade == "d+":
            total_grade += grade_ratio * 1.5
        elif average_grade == "d":
            total_grade += grade_ratio * 1
        elif average_grade == "e":
            total_grade += grade_ratio * 0.5

    if average_total_grade != "Incomplete":
        if total_grade > 3.75:
            average_total_grade = "A"
        elif total_grade >= 3.25:
            average_total_grade = "B+"
        elif total_grade >= 2.75:
            average_total_grade = "B"
        elif total_grade >= 2.25:
            average_total_grade = "C+"
        elif total_grade >= 1.75:
            average_total_grade = "C"
        elif total_grade >= 1.25:
            average_total_grade = "D+"
        elif total_grade >= 0.75:
            average_total_grade = "D"
        else:
            average_total_grade = "E"

    return render_template(
        "/round_grades/view-student.html",
        student=student,
        class_=class_,
        project=project,
        round_grades=round_grades,
        average_total_grade=average_total_grade,
    )
