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


@module.route("/<class_id>/<grade_type>/view")
@login_required
def view(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    grades = models.Grade.objects.all().filter(class_=class_)

    # Create Midterm and Final Grade
    if not grades:
        midterm = models.Grade()
        midterm.type = "midterm"
        midterm.class_ = class_
        midterm.teacher = current_user._get_current_object()
        midterm.save()

        final = models.Grade()
        final.type = "final"
        final.class_ = class_
        final.teacher = current_user._get_current_object()
        final.save()

        for id in class_.student_ids:
            try:
                student = models.User.objects.get(username=id)

            except:
                # Create Dummy for Student that have no account
                student = models.User()
                student.username = id
                student.email = f"{id}@FakeEmail.com"
                student.first_name = ""
                student.last_name = ""
                student.save()

            midterm_Grade = models.StudentGrade()
            midterm_Grade.grade = midterm
            midterm_Grade.student = student
            midterm_Grade.save()
            midterm.student_ids.append(student.username)
            midterm.student_grades.append(midterm_Grade)

            final_Grade = models.StudentGrade()
            final_Grade.grade = final
            final_Grade.student = student
            final_Grade.save()
            final.student_ids.append(student.username)
            final.student_grades.append(final_Grade)

        midterm.save()
        final.save()

    grade = models.Grade.objects.get(type=grade_type, class_=class_)
    # Student grade != Student  (Student was added or removed)

    midterm = models.Grade.objects.get(type="midterm", class_=class_)
    final = models.Grade.objects.get(type="final", class_=class_)

    for student in class_.student_ids:
        # Student Has been 'ADDED' or 'CHANGED'
        if student not in midterm.student_ids:
            try:
                user = models.User.objects.get(username=student)

            except:
                # Create Dummy for Student that have no account
                user = models.User()
                user.username = student
                user.email = f"{student}@FakeEmail.com"
                user.first_name = ""
                user.last_name = ""
                user.save()

            midterm_Grade = models.StudentGrade()
            midterm_Grade.grade = midterm
            midterm_Grade.student = user
            midterm_Grade.save()
            midterm.student_ids.append(user.username)
            midterm.student_grades.append(midterm_Grade)

            final_Grade = models.StudentGrade()
            final_Grade.grade = final
            final_Grade.student = user
            final_Grade.save()
            final.student_ids.append(user.username)
            final.student_grades.append(final_Grade)

    for student in midterm.student_ids:
        # Sudent Has been 'REMOVED'
        if student not in class_.student_ids:
            old_student = models.User.objects.get(student)
            old_midterm_Grade = models.StudentGrade.objects.get(
                student=old_student, grade=midterm
            )
            old_final_Grade = models.StudentGrade.objects.get(
                student=old_student, grade=final
            )

            old_midterm_Grade.delete()
            old_final_Grade.delete()

            index_mid = midterm.student_grades.index(old_midterm_Grade)
            midterm.student_grades.pop(index_mid)
            midterm.student_ids.remove(student)

            index_fin = final.student_grades.index(old_final_Grade)
            final.student_grades.pop(index_fin)
            final.student_ids.remove(student)

    midterm.save()
    final.save()

    grade = models.Grade.objects.get(type=grade_type, class_=class_)

    return render_template(
        "/grades/view.html",
        class_=class_,
        grade=grade,
        grade_type=grade_type,
        get_student_grade=get_student_grade,
    )


@module.route("/<class_id>/<grade_type>/grading", methods=["GET", "POST"])
@login_required
def grading(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    grade = models.Grade.objects.get(type=grade_type, class_=class_)
    student_grades = models.StudentGrade.objects.all().filter(grade=grade)

    if request.method == "POST":
        for student_grade in student_grades:
            result = request.form.get(str(student_grade.id))
            student_grade.result = result
            student_grade.save()

        return redirect(
            url_for("grades.view", class_id=class_.id, grade_type=grade_type)
        )

    return render_template("/grades/view.html", class_=class_, grade=grade)


@module.route("/<class_id>/<grade_type>/total")
@login_required
def total(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    grade = models.Grade.objects.all().filter(class_=class_)
    student_grades = models.StudentGrade.objects.all().filter(grade=grade)

    if request.method == "POST":
        for student_grade in student_grades:
            result = request.form.get(str(student_grade.id))
            student_grade.result = result
            student_grade.save()

        return redirect(
            url_for("grades.view", class_id=class_.id, grade_type=grade_type)
        )

    return render_template("/grades/view.html", class_=class_, grade=grade)
