from wtforms import fields
from wtforms import widgets

from bussaya.forms.projects import BaseProjectForm


from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form

from bussaya import models

BaseProjectForm = model_form(
    models.Meeting,
    FlaskForm,
    exclude=[
        "created_date",
        "updated_date",
        "owner",
        "class_",
        "started_date",
        "ended_date",
        "title",
    ],
    field_args={
        "name": {"label": "Name"},
    },
)


class MeetingForm(BaseProjectForm):
    started_date = fields.DateTimeField(
        "Started Date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )
    ended_date = fields.DateTimeField(
        "Ended date", widget=widgets.TextInput(), format="%Y-%m-%d %H:%M"
    )


class StudentWorkMeetingForm(BaseProjectForm):
    title = fields.StringField("Title")
    description = fields.StringField("Description")
    meeting_date = fields.DateField("Meeting Date", format="%Y-%m-%d")


class DisapproveForm(BaseProjectForm):
    remark = fields.StringField("Disapprove Remark")
