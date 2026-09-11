"""Deadline-reminder email logic.

Sends a reminder email 2 days and 1 day before:
  - a RoundGrade's grading window closes (to lecturers with pending grades)
  - a Meeting's report window closes (to students who haven't submitted)
  - a report Submission's window closes (to students who haven't submitted)
  - a presentation Submission's window closes (to students who haven't submitted)

Designed to be run once a day (e.g. via cron calling
scripts/send_deadline_reminders.py). Idempotent: each (target, recipient,
days_before) combination is recorded in DeadlineNotification so re-running
the job the same day never sends duplicate emails.
"""

import datetime
import logging

from bussaya import models
from bussaya.utils.mailer import Mailer

logger = logging.getLogger(__name__)

REMINDER_DAYS_BEFORE = [2, 1]


def _days_until(target_date):
    return (target_date.date() - datetime.date.today()).days


def _already_notified(target_type, target_id, recipient, days_before):
    return models.DeadlineNotification.objects(
        target_type=target_type,
        target_id=target_id,
        recipient=recipient,
        days_before=days_before,
    ).first()


def _record_notification(target_type, target_id, recipient, days_before, status):
    models.DeadlineNotification(
        target_type=target_type,
        target_id=target_id,
        recipient=recipient,
        days_before=days_before,
        status=status,
    ).save()


def _send_reminder(mailer, target_type, target_id, recipient, days_before, subject, body):
    if _already_notified(target_type, target_id, recipient, days_before):
        return "skipped"

    sent = mailer.send(recipient.email, subject, body)
    _record_notification(
        target_type, target_id, recipient, days_before, "sent" if sent else "failed"
    )
    return "sent" if sent else "failed"


def send_round_grade_reminders(mailer, base_url=""):
    """Email lecturers who still have pending (result == '-') grades in a
    RoundGrade whose grading window closes in 2 or 1 day(s)."""

    counts = {"sent": 0, "failed": 0, "skipped": 0}
    template = models.EmailTemplate.get_or_create_default("round_grade_reminder")

    round_grades = models.RoundGrade.objects(release_status__ne="released")
    for round_grade in round_grades:
        days_before = _days_until(round_grade.ended_date)
        if days_before not in REMINDER_DAYS_BEFORE:
            continue

        class_ = round_grade.class_
        pending = models.StudentGrade.objects(round_grade=round_grade, result="-")

        pending_counts_by_lecturer = {}
        for student_grade in pending:
            lecturer = student_grade.grader.lecturer if student_grade.grader else None
            if not lecturer:
                continue
            pending_counts_by_lecturer[lecturer.id] = (
                pending_counts_by_lecturer.get(lecturer.id, 0) + 1
            )

        for lecturer_id, pending_count in pending_counts_by_lecturer.items():
            lecturer = models.User.objects(id=lecturer_id).first()
            if not lecturer:
                continue

            link = f"{base_url}/round_grades/{round_grade.id}/grading" if base_url else ""
            subject, body = template.render(
                lecturer_name=lecturer.fullname,
                class_name=class_.name,
                round_display=round_grade.get_type_display(),
                deadline=round_grade.natural_ended_date(),
                days_before=days_before,
                pending_count=pending_count,
                link=link,
            )

            result = _send_reminder(
                mailer, "round_grade", round_grade.id, lecturer, days_before, subject, body
            )
            counts[result] += 1

    return counts


def send_meeting_report_reminders(mailer, base_url=""):
    """Email students in a class who haven't submitted their meeting report
    yet for a Meeting whose window closes in 2 or 1 day(s)."""

    counts = {"sent": 0, "failed": 0, "skipped": 0}
    template = models.EmailTemplate.get_or_create_default("meeting_reminder")

    for meeting in models.Meeting.objects:
        days_before = _days_until(meeting.ended_date)
        if days_before not in REMINDER_DAYS_BEFORE:
            continue

        class_ = meeting.class_
        for student in class_.get_students():
            if meeting.get_meeting_report_by_owner(student):
                continue

            link = f"{base_url}/classes/{class_.id}" if base_url else ""
            subject, body = template.render(
                student_name=student.fullname,
                class_name=class_.name,
                round_display=meeting.get_round_display(),
                deadline=meeting.natural_ended_date(),
                days_before=days_before,
                link=link,
            )

            result = _send_reminder(
                mailer, "meeting", meeting.id, student, days_before, subject, body
            )
            counts[result] += 1

    return counts


def _send_submission_reminders(mailer, submission_type, base_url):
    counts = {"sent": 0, "failed": 0, "skipped": 0}
    template = models.EmailTemplate.get_or_create_default(f"{submission_type}_reminder")

    submissions = models.Submission.objects(type=submission_type)
    for submission in submissions:
        days_before = _days_until(submission.ended_date)
        if days_before not in REMINDER_DAYS_BEFORE:
            continue

        class_ = submission.class_
        for student in class_.get_students():
            if submission.get_progress_report_by_owner(student):
                continue

            link = f"{base_url}/classes/{class_.id}" if base_url else ""
            subject, body = template.render(
                student_name=student.fullname,
                class_name=class_.name,
                round_display=submission.get_round_display(),
                deadline=submission.natural_ended_date(),
                days_before=days_before,
                link=link,
            )

            result = _send_reminder(
                mailer, submission_type, submission.id, student, days_before, subject, body
            )
            counts[result] += 1

    return counts


def send_report_reminders(mailer, base_url=""):
    return _send_submission_reminders(mailer, "report", base_url)


def send_presentation_reminders(mailer, base_url=""):
    return _send_submission_reminders(mailer, "presentation", base_url)


def run_deadline_reminders(app):
    mailer = Mailer(app.config)
    base_url = app.config.get("SITE_BASE_URL", "").rstrip("/")

    summary = {}
    summary["round_grade"] = send_round_grade_reminders(mailer, base_url)
    summary["meeting"] = send_meeting_report_reminders(mailer, base_url)
    summary["report"] = send_report_reminders(mailer, base_url)
    summary["presentation"] = send_presentation_reminders(mailer, base_url)

    for target_type, counts in summary.items():
        logger.info(
            "Deadline reminders for %s: sent=%s failed=%s skipped=%s",
            target_type,
            counts["sent"],
            counts["failed"],
            counts["skipped"],
        )

    return summary
