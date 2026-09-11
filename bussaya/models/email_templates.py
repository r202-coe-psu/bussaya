import datetime
import mongoengine as me

EMAIL_TEMPLATE_TYPE = [
    ("round_grade_reminder", "Round Grade Reminder (Lecturer)"),
    ("meeting_reminder", "Meeting Report Reminder (Student)"),
    ("report_reminder", "Report Reminder (Student)"),
    ("presentation_reminder", "Presentation Reminder (Student)"),
]

# Jinja variables available to each template type, shown to admins in the
# edit form so they know what they can reference with {{ variable }}.
EMAIL_TEMPLATE_VARIABLES = {
    "round_grade_reminder": [
        "lecturer_name",
        "class_name",
        "round_display",
        "deadline",
        "days_before",
        "pending_count",
        "link",
    ],
    "meeting_reminder": [
        "student_name",
        "class_name",
        "round_display",
        "deadline",
        "days_before",
        "link",
    ],
    "report_reminder": [
        "student_name",
        "class_name",
        "round_display",
        "deadline",
        "days_before",
        "link",
    ],
    "presentation_reminder": [
        "student_name",
        "class_name",
        "round_display",
        "deadline",
        "days_before",
        "link",
    ],
}

DEFAULT_EMAIL_TEMPLATES = {
    "round_grade_reminder": {
        "subject": (
            "[Bussaya] {{ round_display }} grading for {{ class_name }} "
            "closes in {{ days_before }} day{{ 's' if days_before != 1 else '' }}"
        ),
        "body": (
            "Dear {{ lecturer_name }},\n"
            "\n"
            'The grading window for "{{ class_name }}" ({{ round_display }}) '
            "closes on {{ deadline }} "
            "({{ days_before }} day{{ 's' if days_before != 1 else '' }} from now).\n"
            "\n"
            "You still have {{ pending_count }} student grade"
            "{{ 's' if pending_count != 1 else '' }} pending.\n"
            "{% if link %}\n{{ link }}\n{% endif %}"
        ),
    },
    "meeting_reminder": {
        "subject": (
            "[Bussaya] Meeting report for {{ class_name }} "
            "closes in {{ days_before }} day{{ 's' if days_before != 1 else '' }}"
        ),
        "body": (
            "Dear {{ student_name }},\n"
            "\n"
            'The meeting report window for "{{ class_name }}" ({{ round_display }}) '
            "closes on {{ deadline }} "
            "({{ days_before }} day{{ 's' if days_before != 1 else '' }} from now), "
            "and you have not submitted one yet.\n"
            "{% if link %}\n{{ link }}\n{% endif %}"
        ),
    },
    "report_reminder": {
        "subject": (
            "[Bussaya] Report for {{ class_name }} "
            "closes in {{ days_before }} day{{ 's' if days_before != 1 else '' }}"
        ),
        "body": (
            "Dear {{ student_name }},\n"
            "\n"
            'The report submission window for "{{ class_name }}" ({{ round_display }}) '
            "closes on {{ deadline }} "
            "({{ days_before }} day{{ 's' if days_before != 1 else '' }} from now), "
            "and you have not submitted one yet.\n"
            "{% if link %}\n{{ link }}\n{% endif %}"
        ),
    },
    "presentation_reminder": {
        "subject": (
            "[Bussaya] Presentation for {{ class_name }} "
            "closes in {{ days_before }} day{{ 's' if days_before != 1 else '' }}"
        ),
        "body": (
            "Dear {{ student_name }},\n"
            "\n"
            'The presentation submission window for "{{ class_name }}" ({{ round_display }}) '
            "closes on {{ deadline }} "
            "({{ days_before }} day{{ 's' if days_before != 1 else '' }} from now), "
            "and you have not submitted one yet.\n"
            "{% if link %}\n{{ link }}\n{% endif %}"
        ),
    },
}


class EmailTemplate(me.Document):
    meta = {"collection": "email_templates"}

    type = me.StringField(required=True, unique=True, choices=EMAIL_TEMPLATE_TYPE)
    subject = me.StringField(required=True)
    body = me.StringField(required=True)

    last_updated_by = me.ReferenceField("User", dbref=True)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    def get_variables(self):
        return EMAIL_TEMPLATE_VARIABLES.get(self.type, [])

    def render(self, **context):
        from jinja2 import Template

        subject = Template(self.subject).render(**context)
        body = Template(self.body).render(**context)
        return subject, body

    @classmethod
    def get_or_create_default(cls, template_type):
        template = cls.objects(type=template_type).first()
        if template:
            return template

        defaults = DEFAULT_EMAIL_TEMPLATES[template_type]
        template = cls(
            type=template_type, subject=defaults["subject"], body=defaults["body"]
        )
        template.save()
        return template
