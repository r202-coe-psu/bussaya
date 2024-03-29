from wtforms import fields
from wtforms import validators
from wtforms import widgets
from .fields import TagListField

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form

from bussaya import models

BaseSubmissionForm = model_form(
    models.Submission,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "class_",
        "ip_address",
        "started_date",
        "ended_date",
        "extended_date",
    ],
    field_args={
        "type": {"label": "Type"},
        "round": {"label": "Round"},
        "description": {"label": "Description"},
    },
)


class SubmissionForm(BaseSubmissionForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    extended_date = fields.DateTimeField(
        "Extended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


BaseProgressReportForm = model_form(
    models.ProgressReport,
    FlaskForm,
    exclude=[],
    only=["project", "description"],
    field_args={
        "project": dict(label="Project", label_modifier=lambda p: p.name),
        "description": dict(label="Description"),
    },
)


class ProgressReportForm(BaseProgressReportForm):
    uploaded_file = fields.FileField(
        "Upload File: PDF only", validators=[FileAllowed(["pdf"], "PDF only")]
    )


class ProgressReportDateForm(FlaskForm):
    created_date = fields.DateTimeField(
        "Created Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    updated_date = fields.DateTimeField(
        "Updated Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )

    remark = fields.StringField("Remark", widget=widgets.TextArea())


class AdminProgressReportForm(ProgressReportForm):
    student = fields.SelectField("Student")
    uploaded_date = fields.DateTimeField(
        "Uploaded Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


BaseFinalSubmissionForm = model_form(
    models.FinalSubmission,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "class_",
        "started_date",
        "ended_date",
        "extended_date",
    ],
    field_args={
        "description": {"label": "Description"},
    },
)


class FinalSubmissionForm(BaseFinalSubmissionForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    extended_date = fields.DateTimeField(
        "Extended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


class FinalReportForm(FlaskForm):
    project = fields.SelectField(
        "Project", choices=[("", "Create and select project first")]
    )
    report = fields.FileField(
        "Report: pdf", validators=[FileAllowed(["pdf"], "PDF only")]
    )
    similarity = fields.FileField(
        "Similarity: pdf", validators=[FileAllowed(["pdf"], "PDF only")]
    )
    presentation = fields.FileField(
        "Presentation: pdf", validators=[FileAllowed(["pdf"], "PDF only")]
    )
    poster = fields.FileField(
        "Poster: pdf, png, jpg",
        validators=[FileAllowed(["pdf", "png", "jpg"], "allow pdf, png, jpg")],
    )
    other = fields.FileField(
        "Other: zip 7z tar.gz",
        validators=[FileAllowed(["zip", "7z", "tar.gz"], "allow zip, 7z, tar.gz")],
    )

    git = fields.URLField("Git URL")
    video = fields.URLField("Video URL")
