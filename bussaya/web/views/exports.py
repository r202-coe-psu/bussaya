import datetime
import io
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    request,
    Response,
)
from flask_login import login_required, current_user

import mongoengine as me

import pandas


from bussaya import models
from bussaya.web import acl


module = Blueprint("exports", __name__, url_prefix="/exports")


@module.route("/classes/<class_id>/students")
@acl.roles_required("admin")
def export_students(class_id):
    class_ = models.Class.objects.get(id=class_id)

    data = []
    for sid in class_.student_ids:
        student = models.User.objects(username=sid).first()

        student_data = {"Student ID": sid}
        if student:
            student_data["Name"] = f"{student.first_name} {student.last_name}"
            project = student.get_project()
            if project:
                student_data["Project"] = project.name
                student_data["Advisor"] = ",".join(
                    [
                        f"{advisor.first_name} {advisor.last_name}"
                        for advisor in project.advisors
                    ]
                )

                for i, committee in enumerate(project.committees):
                    student_data[f"Commitee {i+1}"] = committee.get_fullname()

            student_data["Midterm Meeting"] = student.get_meeting_reports(
                class_, "midterm"
            ).count()
            student_data["Midterm Meeting Approve"] = student.get_meeting_reports(
                class_, "midterm", "approved"
            ).count()

            student_data["Midterm Report"] = 0
            if student.get_report(class_, "midterm"):
                student_data["Midterm Report"] = 1

            student_data["Midterm Presentation"] = 0
            if student.get_presentation(class_, "midterm"):
                student_data["Midterm Presentation"] = 1

            student_data["Final Meeting"] = student.get_meeting_reports(
                class_, "final"
            ).count()
            student_data["Final Meeting Approve"] = student.get_meeting_reports(
                class_, "final", "approved"
            ).count()

            student_data["Final Report"] = 0
            if student.get_report(class_, "final"):
                student_data["Final Report"] = 1

            student_data["Final Presentation"] = 0
            if student.get_presentation(class_, "final"):
                student_data["Final Presentation"] = 1

            round_grades = models.RoundGrade.objects(class_=class_)
            for rg in round_grades:
                grade = student.get_actual_grade(rg)
                if rg.type == "midterm":
                    student_data["Midterm Grade"] = grade[0]
                elif rg.type == "final":
                    student_data["Final Grade"] = grade[0]

            student_data["Complete Grade"] = student.get_complete_grade(class_)

        data.append(student_data)

    df = pandas.DataFrame.from_records(data)
    output = io.BytesIO()
    writer = pandas.ExcelWriter(output, engine="xlsxwriter")
    df.index += 1
    df.to_excel(writer, sheet_name="Student")
    writer.save()

    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition": f"attachment; filename=export-students.xlsx"},
    )
