from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm

from bussaya import models

BaseCurriculumForm = model_form(
    models.Curriculum,
    FlaskForm,
    exclude=[
        "status",
        "creator",
        "last_updated_by",
        "created_date",
        "updated_date",
    ],
    field_args={
        "name": {"label": "Name"},
        "name_th": {"label": "Name (Thai)"},
        "code": {"label": "Code"},
    },
)


class CurriculumForm(BaseCurriculumForm):
    pass


BasePLOForm = model_form(
    models.PLO,
    FlaskForm,
    exclude=["curriculum", "status", "created_date", "updated_date"],
    field_args={
        "code": {"label": "Code"},
        "description": {"label": "Description"},
        "description_th": {"label": "Description (Thai)"},
        "order": {"label": "Order"},
    },
)


class PLOForm(BasePLOForm):
    pass


BaseCLOForm = model_form(
    models.CLO,
    FlaskForm,
    exclude=["curriculum", "status", "created_date", "updated_date"],
    field_args={
        "code": {"label": "Code"},
        "description": {"label": "Description"},
        "description_th": {"label": "Description (Thai)"},
        "order": {"label": "Order"},
        "plos": {"label": "Mapped PLOs"},
    },
)


class CLOForm(BaseCLOForm):
    pass
