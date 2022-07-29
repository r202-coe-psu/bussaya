from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl

module = Blueprint("round_grades", __name__, url_prefix="/round_grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/round_grades/index.html", class_=class_)


def get_lecturers_project_of_student(username):
    student = models.User.objects(username=username).first()
    if not student:
        return []

    lecturers = []
    project = student.get_project()
    if project:
        if project.committees:
            lecturers.append(project.advisor)
            for committee in project.committees:
                lecturers.append(committee)
        else:
            lecturers = [project.advisor]

    return lecturers


def create_student_grade(class_, round_grade, student, lecturer):
    student_grade = models.StudentGrade()
    student_grade.class_ = class_
    student_grade.round_grade = round_grade
    student_grade.student = student
    student_grade.lecturer = lecturer
    if student.get_project():
        student_grade.project

    student_grade.save()
    if student.username not in round_grade.student_ids:
        round_grade.student_ids.append(student.username)

    round_grade.student_grades.append(student_grade)
    round_grade.save()


@module.route("/<class_id>/<round_grade_type>/view")
@acl.roles_required("admin")
def view(class_id, round_grade_type):
    class_ = models.Class.objects.get(id=class_id)
    round_grades = models.RoundGrade.objects.all().filter(class_=class_)
    user = current_user._get_current_object()
    # Create Midterm and Final RoundGrade
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
    for id in class_.student_ids:
        student = models.User.objects(username=id).first()
        if not student or not student.has_roles("student"):
            continue

        for lecturer in get_lecturers_project_of_student(student.username):
            if not models.StudentGrade.objects(
                class_=class_, student=student, lecturer=lecturer
            ):
                create_student_grade(class_, midterm, student, lecturer)
                create_student_grade(class_, final, student, lecturer)

    for student_id in midterm.student_ids:
        # Student Has been 'REMOVED'
        if student_id not in class_.student_ids:
            student = models.User.objects(username=student_id).first()
            if not student:
                continue

            old_midterm_Grade = models.StudentGrade.objects(
                student=student, round_grade=midterm, class_=class_
            )
            old_final_Grade = models.StudentGrade.objects(
                student=student, round_grade=final, class_=class_
            )

            old_midterm_Grade.delete()
            old_final_Grade.delete()

            midterm.student_ids.remove(student_id)
            final.student_ids.remove(student_id)

    midterm.save()
    final.save()

    round_grade = models.RoundGrade.objects.get(type=round_grade_type, class_=class_)
    student_grades = models.StudentGrade.objects(
        class_=class_, lecturer=user, round_grade=round_grade
    )

    student_grades = sorted(student_grades, key=lambda s: s.student.username)

    return render_template(
        "/admin/round_grades/view.html",
        user=user,
        class_=class_,
        round_grade=round_grade,
        round_grade_type=round_grade_type,
        student_grades=student_grades,
    )


@module.route("/<class_id>/<round_grade_type>/view_total")
@acl.roles_required("admin")
def view_total(class_id, round_grade_type):
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


@module.route("/<round_grade_id>/grading", methods=["GET", "POST"])
@acl.roles_required("admin")
def grading(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
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

        meetings = models.MeetingReport.objects(
            class_=class_, owner=student_grade.student
        )
        for meeting in meetings:
            meeting.status = "approved"
            meeting.save()
        student_grade.save()

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
