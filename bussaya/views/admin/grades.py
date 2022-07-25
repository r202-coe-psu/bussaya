from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from bussaya import forms, models, acl

module = Blueprint("grades", __name__, url_prefix="/grades")


@module.route("/<class_id>")
@login_required
def index(class_id):
    class_ = models.Class.objects.get(id=class_id)
    return render_template("/grades/index.html", class_=class_)


@module.route("/<class_id>/<grade_type>/view_total")
@acl.roles_required("admin")
def view_total(class_id, grade_type):
    class_ = models.Class.objects.get(id=class_id)
    user = current_user._get_current_object()

    grade = models.Grade.objects.get(type=grade_type, class_=class_)
    total_student_grades = models.StudentGrade.objects(class_=class_, grade=grade)

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
        "/admin/grades/view-total.html",
        user=user,
        class_=class_,
        grade=grade,
        grade_type=grade_type,
        student_grades=student_grades,
    )


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
def change_release_status(grade_id):
    grade = models.Grade.objects.get(id=grade_id)
    grade.release_status = (
        "released" if grade.release_status == "unreleased" else "unreleased"
    )

    grade.save()

    return redirect(
        url_for("grades.view", grade_type=grade.type, class_id=grade.class_.id)
    )
