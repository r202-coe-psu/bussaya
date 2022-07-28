from wtforms import fields
from wtforms import validators
from wtforms import widgets

from .fields import TagListField

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from flask_mongoengine.wtf import model_form


from bussaya import models

BaseProjectForm = model_form(
    models.Project,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "approvals",
        "resources",
        "class_",
        "public",
    ],
    field_args={
        "name": {"label": "English Name"},
        "name_th": {"label": "Thai Name"},
        "abstract": {"label": "English Abstract"},
        "abstract_th": {"label": "Thai Abstract"},
        "advisor": {
            "label": "Advisor",
            "label_modifier": lambda a: f"{a.first_name} {a.last_name}",
        },
        "committees": {
            "label": "Committees",
            "allow_blank": True,
            "blank_text": "There are no committees",
            "label_modifier": lambda a: f"{a.first_name} {a.last_name}",
        },
        "students": {
            "label": "Contributors",
            "allow_blank": True,
            "blank_text": "There are no contributors",
            "label_modifier": lambda a: f"{a.first_name} {a.last_name}",
        },
    },
)


class ProjectForm(BaseProjectForm):
    tags = TagListField(
        "Tags: divied by comma (,)", validators=[validators.length(min=3)]
    )
    # class_ = fields.SelectField("Class", validators=[validators.InputRequired()])
    # contributors = fields.SelectField(
    #     "Contributors", default=None, choices=[("", "If your project has contributor")]
    # )
    # advisor = fields.SelectField("Advisor", validators=[validators.InputRequired()])

    # committees = fields.SelectMultipleField(
    #     "Committees",
    #     validators=[validators.length(max=5, min=0)],
    # )


class ProjectResourceUploadForm(FlaskForm):
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
