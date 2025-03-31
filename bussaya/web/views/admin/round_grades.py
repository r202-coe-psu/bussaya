import datetime
import markdown
from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_login import login_required, current_user
from PyPDF2 import PdfReader, PdfWriter
import io
import tempfile
import os


import mongoengine as me

from bussaya import models
from bussaya.web import forms, acl
from bussaya import utils


module = Blueprint("round_grades", __name__, url_prefix="/round_grades")


def get_lecturers_project_of_student(student):
    lecturers = []
    if not student:
        return lecturers
    project = student.get_project()
    if project:
        for advisor in project.advisors:
            lecturers.append(advisor)
        for committee in project.committees:
            lecturers.append(committee)

    return lecturers


def create_student_grade(round_grade, student, lecturer):
    grader = models.Grader(lecturer=lecturer)
    student_grade = models.StudentGrade(
        class_=round_grade.class_,
        round_grade=round_grade,
        student=student,
        grader=grader,
    )
    if not student:
        return

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
                grader__lecturer=lecturer,
                round_grade=round_grade,
                project=student.get_project(),
            ):
                create_student_grade(round_grade, student, lecturer)


def get_grading_student(class_, lecturer):
    students = models.User.objects(username__in=class_.student_ids)
    projects = models.Project.objects(
        (me.Q(creator__in=students) | me.Q(students__in=students))
        & (me.Q(advisors=lecturer) | me.Q(committees=lecturer)),
        status="active",
    )
    grading_students = []
    for p in projects:
        if p.creator not in grading_students:
            grading_students.append(p.creator)

        for s in p.students:
            if s not in grading_students:
                grading_students.append(s)

    return grading_students


def check_and_create_student_grade_profile(round_grade, lecturer):
    student_grades = models.StudentGrade.objects(
        grader__lecturer=lecturer, round_grade=round_grade
    )

    for student_grade in student_grades:
        projects = models.Project.objects(
            me.Q(students=student_grade.student)
            & (me.Q(advisors=lecturer) | me.Q(committees=lecturer)),
            status="active",
        )
        if not projects:
            student_grade.delete()

    for student in get_grading_student(round_grade.class_, lecturer):
        if not models.StudentGrade.objects(
            class_=round_grade.class_,
            student=student,
            grader__lecturer=lecturer,
            round_grade=round_grade,
        ).first():
            create_student_grade(round_grade, student, lecturer)


def check_and_create_mentor_grade_profile(round_grade):
    student_grades = models.StudentGrade.objects(
        grader__mentor__ne=None, round_grade=round_grade
    )
    class_ = round_grade.class_

    for student_grade in student_grades:
        projects = models.Project.objects(
            me.Q(students=student_grade.student),
            status="active",
        )
        if not projects:
            student_grade.delete()

    students = models.User.objects(username__in=class_.student_ids)
    projects = models.Project.objects(
        (me.Q(creator__in=students) | me.Q(students__in=students)),
        status="active",
    )

    grading_students = []
    for p in projects:
        if p.creator not in grading_students:
            grading_students.append(p.creator)

        for s in p.students:
            if s not in grading_students:
                grading_students.append(s)

    for student in grading_students:
        if (
            student
            and not models.StudentGrade.objects(
                class_=round_grade.class_,
                student=student,
                round_grade=round_grade,
                project=student.get_project(),
                grader__lecturer=None,
            ).first()
        ):
            student_grade = models.StudentGrade(
                class_=round_grade.class_,
                student=student,
                project=student.get_project(),
                round_grade=round_grade,
            )
            student_grade.save()


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
        grader__lecturer=current_user._get_current_object(),
        round_grade=round_grade,
    )
    student_grades = sorted(
        student_grades,
        key=lambda s: (
            [advisor.username for advisor in s.project.advisors],
            s.student.username,
        ),
    )

    return render_template(
        "/admin/round_grades/view.html",
        user=current_user,
        class_=class_,
        round_grade=round_grade,
        round_grade_type=round_grade_type,
        student_grades=student_grades,
    )


@module.route("/<round_grade_type>/approve_report")
@acl.roles_required("admin")
def approve_report(round_grade_type):
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

    signatures = []

    for student_grade in student_grades:
        report = student_grade.student.get_report(class_, round_grade.type)
        if report and report.file:
            try:
                # ดึงเนื้อหาของไฟล์จาก GridFS
                file_content = report.file.read()  # ใช้ read() เพื่อดึงเนื้อหาของไฟล์
                
                # ตรวจสอบใบรับรองในไฟล์ PDF
                signature = utils.verrify_pdf.extract_certificates(file_content, 'bussaya/certificate/certificate_key.pem')
                signatures.append(signature)

            except Exception as e:

                '''   
                debug code

                print(f"❌ ไม่สามารถอ่านไฟล์ PDF: {e}")   
                '''

                signatures.append(None)
        else:

            '''  
            debug code

            print("❌ ไม่พบไฟล์ในรายงาน")  
            '''
            
            signatures.append(None)

    # print(signatures)
    # print(user)
    return render_template(
        "/admin/round_grades/approve-report.html",
        user=current_user,
        class_=class_,
        round_grade=round_grade,
        round_grade_type=round_grade_type,
        student_grades=student_grades,
        signatures=signatures,
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


@module.route("/<round_grade_type>/view_grade_summary")
@acl.roles_required("admin")
def view_grade_summary(round_grade_type):
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
        "/admin/round_grades/view-grade-summary.html",
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
        class_=class_, round_grade=round_grade, grader__lecturer__ne=None
    )
    lecturers = set([s.grader.lecturer for s in total_student_grades])
    lecturers = sorted(lecturers, key=lambda l: (l.first_name, l.last_name))

    # print([lec.first_name for lec in lecturers])

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
    check_and_create_student_grade_profile(round_grade, user)
    student_grades = models.StudentGrade.objects.all().filter(
        round_grade=round_grade, grader__lecturer=user
    )
    student_grades = sorted(student_grades, key=lambda s: (s.student.username))

    student_grades = sorted(
        student_grades,
        key=lambda s: (
            [advisor.username for advisor in s.project.advisors],
            s.student.username,
        ),
    )

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


@module.route("/<round_grade_id>/submit-grade", methods=["GET", "POST"])
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
        student = models.User.objects.get(id=grading["student_id"])
        student_grade = models.StudentGrade.objects(
            student=student,
            class_=class_,
            round_grade=round_grade,
            grader__lecturer=user,
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


@module.route("/<round_grade_id>/submit-mentor-grade", methods=["GET", "POST"])
@acl.roles_required("admin")
def submit_mentor_grade(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    class_ = round_grade.class_
    user = current_user._get_current_object()
    # student_grades = models.StudentGrade.objects(round_grade=round_grade, lecturer=user)

    check_and_create_mentor_grade_profile(round_grade)
    student_grades = models.StudentGrade.objects.filter(
        round_grade=round_grade, grader__lecturer=None
    )
    student_grades = sorted(student_grades, key=lambda s: (s.student.username))

    student_grades = sorted(
        student_grades,
        key=lambda s: (s.student.username,),
    )
    form = forms.round_grades.GroupMentorGradingForm()

    mentors = models.Mentor.objects(status="active")
    mentor_choices = [
        (str(mentor.id), f"{mentor.name} - {mentor.organization.name}")
        for mentor in mentors
    ]
    mentor_choices = [("-", "-")] + mentor_choices

    for i, s in enumerate(student_grades):
        if request.method == "GET":
            form.gradings.append_entry(
                {
                    "student_id": str(s.student.id),
                    "result": s.result,
                    "mentor_id": (
                        str(s.grader.mentor.id) if s.grader and s.grader.mentor else ""
                    ),
                }
            )
        form.gradings[i].mentor_id.choices = mentor_choices

    if not form.validate_on_submit():
        return render_template(
            "/admin/round_grades/submit-mentor-grade.html",
            class_=class_,
            round_grade=round_grade,
            form=form,
            student_grades=student_grades,
        )

    for grading in form.gradings.data:
        student = models.User.objects.get(id=grading["student_id"])
        mentor = None

        if grading["mentor_id"] != "-":
            mentor = models.Mentor.objects(id=grading["mentor_id"]).first()

        project = student.get_project()
        student_grade = models.StudentGrade.objects(
            student=student,
            class_=class_,
            project=project,
            round_grade=round_grade,
            grader__lecturer=None,
        ).first()

        if not student_grade:
            continue

        student_grade.result = grading["result"]
        student_grade.grader.mentor = mentor
        student_grade.updated_date = datetime.datetime.now()

        student_grade.save()

    return redirect(
        url_for(
            "admin.round_grades.view",
            class_id=class_.id,
            round_grade_type=round_grade.type,
        )
    )


@module.route("/<round_grade_id>/set-time", methods=["GET", "POST"])
@acl.roles_required("admin")
def set_time(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    round_grade_type = round_grade.type
    class_ = round_grade.class_
    form = forms.round_grades.RoundGradeForm(obj=round_grade)

    # print(round_grade.started_date)
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


@module.route("/<round_grade_id>/reset-grading")
@acl.roles_required("admin")
def reset_grading(round_grade_id):
    round_grade = models.RoundGrade.objects.get(id=round_grade_id)
    round_grade_type = round_grade.type
    class_ = round_grade.class_

    lecturers = models.User.objects(roles="lecturer")

    for user in lecturers:
        check_and_create_student_grade_profile(round_grade, user)

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


@module.route(
    "/<class_id>/<round_grade_type>/view_advisor_students/<advisor_id>",
    methods=["GET", "POST"],
)
@acl.roles_required("admin")
def view_advisor_students(round_grade_type, class_id, advisor_id):
    advisor = models.User.objects.get(id=advisor_id)

    class_ = models.Class.objects.get(id=class_id)
    student_ids = class_.student_ids
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

    project_infos = []

    for student_grade in student_grades:
        student = student_grade.student
        if advisor in student.get_project().advisors:
            project_infos.append(
                {
                    "project": student.get_project(),
                    "student": student,
                }
            )

    return render_template(
        "admin/round_grades/view-advisor-students.html",
        advisor=advisor,
        round_grade_type=round_grade_type,
        round_grade=round_grade,
        class_=class_,
        student_grades=student_grades,
        project_infos=project_infos,
    )
