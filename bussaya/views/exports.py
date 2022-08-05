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

from bussaya import acl

import datetime
import pandas
import io
from .. import models

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
            student_data["Midterm Meeting"] = student.get_meeting_reports(
                class_, "midterm"
            ).count()
            student_data["Final Meeting"] = student.get_meeting_reports(
                class_, "final"
            ).count()
            if project:
                student_data[
                    "Advisor"
                ] = f"{project.advisor.first_name} {project.advisor.last_name}"

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
