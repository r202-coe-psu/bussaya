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
    student_projects = models.Project.objects(class_=class_)
    for project in student_projects:
        if student in project.students:
            student_grade.project = project

    student_grade.save()
    if student.username not in round_grade.student_ids:
        round_grade.student_ids.append(student.username)

    round_grade.student_grades.append(student_grade)
    round_grade.save()


@module.route("/<class_id>/<round_grade_type>/view")
@acl.roles_required("lecturer")
def view(class_id, round_grade_type):
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

    print(form.data)

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
    # student_grades = models.StudentGrade.objects(round_grade=round_grade, lecturer=user)

    form = forms.round_grades.GroupGradingForm()
    if not form.validate_on_submit():
        return redirect(url_for("round_grades.grading", round_grade_id=round_grade_id))

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

    return redirect(url_for("round_grades.grading", round_grade_id=round_grade.id))


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
        if average_grade == "b+":
            total_grade += grade_ratio * 3.5
        if average_grade == "b":
            total_grade += grade_ratio * 3
        if average_grade == "c+":
            total_grade += grade_ratio * 2.5
        if average_grade == "c":
            total_grade += grade_ratio * 2
        if average_grade == "d+":
            total_grade += grade_ratio * 1.5
        if average_grade == "d":
            total_grade += grade_ratio * 1
        if average_grade == "e":
            total_grade += grade_ratio * 0

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
        elif total_grade < 0.5:
            average_total_grade = "E"

    return render_template(
        "/round_grades/view-student.html",
        student=student,
        class_=class_,
        project=project,
        round_grades=round_grades,
        average_total_grade=average_total_grade,
    )
