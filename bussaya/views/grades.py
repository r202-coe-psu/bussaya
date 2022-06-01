from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl

module = Blueprint("grades", __name__, url_prefix="/grades")


@module.route("/<class_id>")
@login_required
@acl.roles_required("admin", "lecturer")
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/grades/index.html", class_=class_)


def get_user_by_username(username):
    user = models.User.objects.get(username=username)
    return user


def get_student_grade(username, grade):
    user = models.User.objects.get(username=username)
    student_grade = models.StudentGrade.objects.get(
        grade=grade,
        student=user,
    )
    return student_grade


@module.route("/<class_id>/<grade_type>")
@login_required
@acl.roles_required("admin", "lecturer")
def view(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    grades = models.Grade.objects.all().filter(class_=class_)

    # Create Midterm and Final Grade
    if not grades:
        midterm = models.Grade()
        midterm.type = "midterm"
        midterm.class_ = class_

        final = models.Grade()
        final.type = "final"
        final.class_ = class_
        midterm.save()
        final.save()

        for id in class_.student_ids:
            student = get_user_by_username(id)

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

    grade = models.Grade.objects.get(type=grade_type)

    # Student grade != Student  (Student was added or removed)
    student_amount = len(class_.student_ids)
    grade_amount = len(grade.student_grades)

    midterm = models.Grade.objects.get(type="midterm", class_=class_)
    final = models.Grade.objects.get(type="final", class_=class_)

    for student in class_.student_ids:
        # Student Has been 'ADDED' or 'CHANGED'
        if student not in midterm.student_ids:
            user = get_user_by_username(student)

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
            old_student = get_user_by_username(student)
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

    grade = models.Grade.objects.get(type=grade_type)

    return render_template(
        "/grades/view.html",
        class_=class_,
        grade=grade,
        grade_type=grade_type,
        get_user_by_username=get_user_by_username,
        get_student_grade=get_student_grade,
    )
