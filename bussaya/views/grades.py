from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl

module = Blueprint("grades", __name__, url_prefix="/grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/grades/index.html", class_=class_)


def get_total_student_grades(student, grade):
    student_grades = models.StudentGrade.objects.all().filter(
        student=student, class_=grade.class_, grade=grade
    )
    return student_grades


def get_average_grade(student, grade):
    student_grades = models.StudentGrade.objects.all().filter(
        student=student, class_=grade.class_, grade=grade
    )

    total_student_grade = []
    for student_grade in student_grades:
        if student_grade.result != "-":
            total_student_grade.append(student_grade)

    if len(total_student_grade) < 2:
        return "Inconclusive"

    average_point = 0
    committees_grade_point = 0

    project = student.get_project()

    if len(project.committees) > 1:
        advisor_grade_ratio = 0.5
        committee_grade_ratio = 0.5
    else:
        advisor_grade_ratio = 0.6
        committee_grade_ratio = 0.4

    for grade in total_student_grade:
        grade_point = grade.get_grade_point()
        if grade.lecturer in project.committees:
            committees_grade_point += grade_point

        else:
            average_point += advisor_grade_ratio * grade_point

    average_point += committee_grade_ratio * committees_grade_point

    if average_point < 80:
        average_grade = "A"
    if 79 >= average_point >= 75:
        average_grade = "B+"
    if 74 >= average_point >= 70:
        average_grade = "B"
    if 69 >= average_point >= 65:
        average_grade = "C+"
    if 64 >= average_point >= 60:
        average_grade = "C"
    if 59 >= average_point >= 55:
        average_grade = "D+"
    if 54 >= average_point >= 50:
        average_grade = "D"
    if average_point < 50:
        average_grade = "E"

    return average_grade


def get_student_report(username, class_id):
    class_ = models.Class.objects.get(id=class_id)
    owner = models.User.objects.get(username=username)
    progress_reports = models.ProgressReport.objects(class_=class_, owner=owner)

    for progress_report in progress_reports:
        if progress_report.submission.type == "report":
            return progress_report
    return False


def get_student_presentation(username, class_id):
    class_ = models.Class.objects.get(id=class_id)
    owner = models.User.objects.get(username=username)
    progress_reports = models.ProgressReport.objects(class_=class_, owner=owner)

    for progress_report in progress_reports:
        if progress_report.submission.type == "presentation":
            return progress_report
    return False


def get_lecturers_project_of_student(username):
    student = models.User.objects.get(username=username)
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
    current_lecturer = current_user._get_current_object()
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

        project_lecturers = []

        for id in class_.student_ids:
            student = models.User.objects(username=id).first()
            if not student or not student.has_roles("student"):
                continue

            for lecturer in get_lecturers_project_of_student(student.username):
                create_student_grade(class_, midterm, student, lecturer)
                create_student_grade(class_, final, student, lecturer)

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
                print("Create Grade {student.frsit_name} for {lecturer.first_name}")
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

            print("Delete {student_id} for Midterm and Final")

    midterm.save()
    final.save()

    grade = models.Grade.objects.get(type=grade_type, class_=class_)
    student_grades = models.StudentGrade.objects.all().filter(
        grade=grade, lecturer=current_lecturer
    )
    student_grades = sorted(student_grades, key=lambda s: s.student.username)

    if current_user.has_roles("admin"):
        grade_html = "/admin/grades/view.html"
    else:
        grade_html = "/grades/view.html"

    return render_template(
        grade_html,
        user=current_lecturer,
        class_=class_,
        grade=grade,
        grade_type=grade_type,
        student_grades=student_grades,
        get_total_student_grades=get_total_student_grades,
        get_average_grade=get_average_grade,
        get_student_report=get_student_report,
        get_student_presentation=get_student_presentation,
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
        get_total_student_grades=get_total_student_grades,
        get_average_grade=get_average_grade,
        get_student_report=get_student_report,
        get_student_presentation=get_student_presentation,
    )


def get_entire_student_grade(grade, student):
    student_grades = models.StudentGrade.objects.all().filter(
        grade=grade, student=student
    )
    return [grade.result for grade in student_grades]


@module.route("/<grade_id>/set_time", methods=["GET", "POST"])
@acl.roles_required("admin")
def set_time(grade_id):
    grade = models.Grade.objects.get(id=grade_id)
    grade_type = grade.type
    class_ = grade.class_
    form = forms.grades.GradeForm(obj=grade)
    if request.method == "POST":
        form.populate_obj(grade)
        grade.save()
        return redirect(
            url_for("grades.view", grade_type=grade.type, class_id=class_.id)
        )

    return render_template(
        "admin/grades/set-time.html",
        form=form,
        class_=class_,
        grade=grade,
        grade_type=grade.type,
    )


@module.route("/<grade_id>/release", methods=["GET", "POST"])
@acl.roles_required("admin")
def release(grade_id):
    grade = models.Grade.objects.get(id=grade_id)
    grade.release_status = "released"
    grade.save()

    print(grade.release_status)

    return redirect(
        url_for("grades.view", grade_type=grade.type, class_id=grade.class_.id)
    )


@module.route("/<class_id>/grades/view-total-grade")
@acl.roles_required("student")
def view_student_grades(class_id):
    student = current_user._get_current_object()
    class_ = models.Class.objects.get(id=class_id)

    project = student.get_project()
    grades = models.Grade.objects.all().filter(class_=class_)

    return render_template(
        "/grades/view-student.html",
        student=student,
        class_=class_,
        project=project,
        grades=grades,
        get_average_grade=get_average_grade,
    )
