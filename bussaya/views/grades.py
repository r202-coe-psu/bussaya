from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl

module = Blueprint("grades", __name__, url_prefix="/grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/grades/index.html", class_=class_)


def get_lecturers_project_of_student(username):
    student = models.User.objects(username=username).first()
    if not student:
        return []

    lecturers = []
    project = student.get_project()
    if project:
        if project.committees:
            lecturers = project.committees
            lecturers.append(project.advisor)
        else:
            lecturers = [project.advisor]

    return lecturers


def create_student_grade(class_, grade, student, lecturer):
    student_grade = models.StudentGrade()
    student_grade.class_ = class_
    student_grade.grade = grade
    student_grade.student = student
    student_grade.lecturer = lecturer
    student_projects = models.Project.objects(class_=class_)
    for project in student_projects:
        if student in project.students:
            student_grade.project = project

    student_grade.save()
    if student.username not in grade.student_ids:
        grade.student_ids.append(student.username)

    grade.student_grades.append(student_grade)
    grade.save()


@module.route("/<class_id>/<grade_type>/view")
@login_required
def view(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    grades = models.Grade.objects.all().filter(class_=class_)
    user = current_user._get_current_object()
    # Create Midterm and Final Grade
    if not grades:
        midterm = models.Grade()
        midterm.type = "midterm"
        midterm.class_ = class_
        midterm.save()

        final = models.Grade()
        final.type = "final"
        final.class_ = class_
        final.save()

        midterm.save()
        final.save()

    midterm = models.Grade.objects.get(type="midterm", class_=class_)
    final = models.Grade.objects.get(type="final", class_=class_)

    # Project create after grade has been created.
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
                student=student, grade=midterm, class_=class_
            )
            old_final_Grade = models.StudentGrade.objects(
                student=student, grade=final, class_=class_
            )

            old_midterm_Grade.delete()
            old_final_Grade.delete()

            midterm.student_ids.remove(student_id)
            final.student_ids.remove(student_id)

    midterm.save()
    final.save()

    grade = models.Grade.objects.get(type=grade_type, class_=class_)
    student_grades = models.StudentGrade.objects(
        class_=class_, lecturer=user, grade=grade
    )

    student_grades = sorted(student_grades, key=lambda s: s.student.username)

    if current_user.has_roles("admin"):
        grade_html = "/admin/grades/view.html"
    else:
        grade_html = "/grades/view.html"

    return render_template(
        grade_html,
        user=user,
        class_=class_,
        grade=grade,
        grade_type=grade_type,
        student_grades=student_grades,
    )


@module.route("/<grade_id>/grading", methods=["GET", "POST"])
@login_required
def grading(grade_id):
    grade = models.Grade.objects.get(id=grade_id)
    class_ = grade.class_
    user = current_user._get_current_object()
    student_grades = models.StudentGrade.objects.all().filter(
        grade=grade, lecturer=user
    )
    student_grades = sorted(student_grades, key=lambda s: s.student.username)

    if current_user.has_roles("admin"):
        grade_html = "/admin/grades/view.html"
    else:
        grade_html = "/grades/view.html"

    if request.method == "POST":
        if not grade.is_in_time():
            return redirect(
                url_for(grade_html, class_id=class_.id, grade_type=grade.type)
            )

        else:
            for student_grade in student_grades:
                result = request.form.get(str(student_grade.id))
                student_grade.result = result

                get_lecturers_project_of_student(student_grade.student.username)

                if result != "-":
                    meetings = models.MeetingReport.objects(
                        class_=class_, owner=student_grade.student
                    )
                    for meeting in meetings:
                        meeting.status = "approved"
                        meeting.save()
                student_grade.save()

        return redirect(
            url_for("grades.view", class_id=class_.id, grade_type=grade.type)
        )

    return render_template(
        grade_html,
        class_=class_,
        grade=grade,
        user=user,
        student_grades=student_grades,
    )


@module.route("/<class_id>/grades/view-total-grade")
@acl.roles_required("student")
def view_student_grades(class_id):
    student = current_user._get_current_object()
    class_ = models.Class.objects.get(id=class_id)

    project = student.get_project()
    grades = models.Grade.objects.all().filter(class_=class_)

    total_grade = 0
    for grade in grades:
        average_grade = student.get_average_grade(grade).lower()
        if grade.type == "midterm":
            grade_ratio = 0.4
        if grade.type == "final":
            grade_ratio = 0.6

        if average_grade == "incomplete":
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
        "/grades/view-student.html",
        student=student,
        class_=class_,
        project=project,
        grades=grades,
        average_total_grade=average_total_grade,
    )
