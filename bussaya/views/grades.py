from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl

module = Blueprint("grades", __name__, url_prefix="/grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/grades/index.html", class_=class_)


def get_student_grade(username, grade):

    user = models.User.objects.get(username=username)
    student_grade = models.StudentGrade.objects.get(
        grade=grade,
        student=user,
    )
    return student_grade


def create_student_grade(class_, grade, student, teacher):
    print(f"Create {grade.type} for {student.username} by {teacher.username}")
    student_grade = models.StudentGrade()
    student_grade.class_ = class_
    student_grade.grade = grade
    student_grade.student = student
    student_grade.teacher = teacher

    student_projects = models.Project.objects(class_=class_)
    for project in student_projects:
        if student in project.students:
            student_grade.project = project

    student_grade.save()
    if student.username not in grade.student_ids:
        grade.student_ids.append(student.username)
    grade.student_grades.append(student_grade)
    grade.save()

    return student_grade


def get_total_student_grades(student, class_, grade):
    student_grades = models.StudentGrade.objects.all().filter(
        student=student, class_=class_, grade=grade
    )
    return student_grades


@module.route("/<class_id>/<grade_type>/view")
@login_required
def view(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    grades = models.Grade.objects.all().filter(class_=class_)
    current_teacher = current_user._get_current_object()
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

        for id in class_.student_ids:
            user = models.User.objects(username=id).first()
            if not user:
                continue
            if "student" in user.roles:
                create_student_grade(class_, midterm, user, current_teacher)
                create_student_grade(class_, final, user, current_teacher)

        midterm.save()
        final.save()

    midterm = models.Grade.objects.get(type="midterm", class_=class_)
    final = models.Grade.objects.get(type="final", class_=class_)
    # Check current teacher has student grade yet?
    student_grades_in_class = models.StudentGrade.objects.all().filter(class_=class_)
    teacher_in_class = []
    for student_grade in student_grades_in_class:
        if student_grade.teacher not in teacher_in_class:
            teacher_in_class.append(student_grade.teacher)

    student_grades_filter_by_current_teacher = models.StudentGrade.objects.all().filter(
        class_=class_, teacher=current_teacher
    )
    if not student_grades_filter_by_current_teacher:
        for id in class_.student_ids:
            student = models.User.objects(username=id).first()
            if not student:
                continue

            if "student" in student.roles:
                create_student_grade(class_, midterm, student, current_teacher)
                create_student_grade(class_, final, student, current_teacher)

    for student_id in class_.student_ids:
        # Student Has been 'ADDED' or 'CHANGED'
        if student_id not in midterm.student_ids:
            user = models.User.objects(username=student_id).first()
            if not user:
                continue

            for teacher in teacher_in_class:
                teacher_student_ids = []
                student_grades = models.StudentGrade.objects.all().filter(
                    class_=class_, student=user, teacher=teacher
                )
                for student_grade in student_grades:
                    teacher_student_ids.append(student_grade.student.username)

                if student_id not in teacher_student_ids:
                    if "student" in user.roles:
                        create_student_grade(class_, midterm, user, teacher)
                        create_student_grade(class_, final, user, teacher)

    for student_id in midterm.student_ids:
        # Student Has been 'REMOVED'
        if student_id not in class_.student_ids:
            old_student = models.User.objects(username=student_id).first()
            if not old_student:
                continue

            old_midterm_Grade = models.StudentGrade.objects(
                student=old_student, grade=midterm, class_=class_
            )
            old_final_Grade = models.StudentGrade.objects(
                student=old_student, grade=final, class_=class_
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
        grade=grade, teacher=current_teacher
    )
    return render_template(
        "/grades/view.html",
        user=current_teacher,
        class_=class_,
        grade=grade,
        grade_type=grade_type,
        get_student_grade=get_student_grade,
        student_grades=student_grades,
        get_total_student_grades=get_total_student_grades,
    )


@module.route("/<class_id>/<grade_type>/grading", methods=["GET", "POST"])
@login_required
def grading(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    grade = models.Grade.objects.get(type=grade_type, class_=class_)
    user = current_user._get_current_object()
    student_grades = models.StudentGrade.objects.all().filter(grade=grade, teacher=user)

    if request.method == "POST":
        for student_grade in student_grades:
            result = request.form.get(str(student_grade.id))
            print(result)
            student_grade.result = result
            student_grade.save()

        test = request.form.get("test")
        print(test)
        return redirect(
            url_for("grades.view", class_id=class_.id, grade_type=grade_type)
        )

    return render_template(
        "/grades/view.html",
        class_=class_,
        grade=grade,
        user=user,
        student_grades=student_grades,
        get_total_student_grades=get_total_student_grades,
    )


def get_entire_student_grade(grade, student):
    student_grades = models.StudentGrade.objects.all().filter(
        grade=grade, student=student
    )
    return [grade.result for grade in student_grades]
