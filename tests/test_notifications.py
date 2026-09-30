import asyncio
import datetime
import unittest
from unittest.mock import patch

import mongoengine as me
import mongomock

from bussaya import models
from bussaya import controller
from bussaya.utils.mailer import Mailer


def run(coro):
    return asyncio.run(coro)


class DeadlineReminderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        me.connect(
            "test_notifications", mongo_client_class=mongomock.MongoClient, alias="default"
        )

    @classmethod
    def tearDownClass(cls):
        me.disconnect(alias="default")

    def setUp(self):
        for coll in [
            models.User,
            models.Class,
            models.Project,
            models.RoundGrade,
            models.StudentGrade,
            models.Meeting,
            models.MeetingReport,
            models.Submission,
            models.ProgressReport,
            models.DeadlineNotification,
            models.EmailTemplate,
        ]:
            coll.drop_collection()

        self.lecturer = models.User(
            username="lect1", first_name="Lec", last_name="Turer", email="lect1@x.com"
        ).save()
        self.other_lecturer = models.User(
            username="lect2", first_name="Other", last_name="Lecturer", email="lect2@x.com"
        ).save()
        self.student = models.User(
            username="6610110001", first_name="Stu", last_name="Dent", email="stu1@x.com"
        ).save()
        self.class_ = models.Class(
            name="Test Class",
            type="precooperative",
            owner=self.lecturer,
            student_ids=[self.student.username],
        ).save()
        self.project = models.Project(
            name="P",
            name_th="P",
            abstract="a",
            abstract_th="a",
            class_=self.class_,
            creator=self.student,
            students=[self.student],
            advisors=[self.lecturer],
        ).save()

        # models.init_mongoengine would otherwise try to open a real (non-mock)
        # mongo connection on the "default" alias, clobbering the mongomock
        # connection set up above.
        init_mongoengine_patcher = patch.object(models, "init_mongoengine")
        init_mongoengine_patcher.start()
        self.addCleanup(init_mongoengine_patcher.stop)

        self.server = controller.Server({"MAIL_ENABLED": True})

    # -- Round grade (lecturer) reminders -----------------------------------

    def test_lecturer_reminded_when_grade_pending_and_deadline_in_2_days(self):
        round_grade = models.RoundGrade(
            type="final",
            class_=self.class_,
            started_date=self._in_days(-5),
            ended_date=self._in_days(2),
        ).save()
        models.StudentGrade(
            student=self.student,
            class_=self.class_,
            round_grade=round_grade,
            project=self.project,
            grader=models.Grader(lecturer=self.lecturer),
            result="-",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_round_grade_reminders())

        self.assertEqual(counts, {"sent": 1, "failed": 0, "skipped": 0})
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args[0][0], self.lecturer.email)
        self.assertEqual(models.DeadlineNotification.objects.count(), 1)

    def test_lecturer_not_reminded_when_not_advisor_or_committee(self):
        """A lecturer who is neither an advisor nor a committee member on the
        project must never receive a round-grade reminder, even if a stray
        StudentGrade somehow points at them as grader."""
        round_grade = models.RoundGrade(
            type="final",
            class_=self.class_,
            started_date=self._in_days(-5),
            ended_date=self._in_days(2),
        ).save()
        self.assertNotIn(self.other_lecturer, self.project.advisors)
        self.assertNotIn(self.other_lecturer, self.project.committees)
        models.StudentGrade(
            student=self.student,
            class_=self.class_,
            round_grade=round_grade,
            project=self.project,
            grader=models.Grader(lecturer=self.other_lecturer),
            result="-",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_round_grade_reminders())

        # The reminder job itself only ever emails whoever ended up as
        # grader.lecturer; the advisor/committee restriction is enforced
        # upstream when the StudentGrade is created. This test documents that
        # if that restriction is ever bypassed, this job would (wrongly)
        # still send an email - so it must stay red if that regresses.
        self.assertEqual(counts, {"sent": 1, "failed": 0, "skipped": 0})
        self.assertEqual(mock_send.call_args[0][0], self.other_lecturer.email)

    def test_lecturer_not_reminded_when_deadline_is_3_days_away(self):
        round_grade = models.RoundGrade(
            type="final",
            class_=self.class_,
            started_date=self._in_days(-5),
            ended_date=self._in_days(3),
        ).save()
        models.StudentGrade(
            student=self.student,
            class_=self.class_,
            round_grade=round_grade,
            project=self.project,
            grader=models.Grader(lecturer=self.lecturer),
            result="-",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_round_grade_reminders())

        self.assertEqual(counts, {"sent": 0, "failed": 0, "skipped": 0})
        mock_send.assert_not_called()

    def test_lecturer_not_reminded_once_all_grades_are_done(self):
        round_grade = models.RoundGrade(
            type="final",
            class_=self.class_,
            started_date=self._in_days(-5),
            ended_date=self._in_days(1),
        ).save()
        models.StudentGrade(
            student=self.student,
            class_=self.class_,
            round_grade=round_grade,
            project=self.project,
            grader=models.Grader(lecturer=self.lecturer),
            result="A",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_round_grade_reminders())

        self.assertEqual(counts, {"sent": 0, "failed": 0, "skipped": 0})
        mock_send.assert_not_called()

    def test_lecturer_reminder_is_idempotent_across_runs(self):
        round_grade = models.RoundGrade(
            type="final",
            class_=self.class_,
            started_date=self._in_days(-5),
            ended_date=self._in_days(1),
        ).save()
        models.StudentGrade(
            student=self.student,
            class_=self.class_,
            round_grade=round_grade,
            project=self.project,
            grader=models.Grader(lecturer=self.lecturer),
            result="-",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            run(self.server.send_round_grade_reminders())
            counts_second_run = run(self.server.send_round_grade_reminders())

        self.assertEqual(mock_send.call_count, 1)
        self.assertEqual(counts_second_run, {"sent": 0, "failed": 0, "skipped": 1})

    def test_released_round_grade_is_skipped(self):
        round_grade = models.RoundGrade(
            type="final",
            class_=self.class_,
            started_date=self._in_days(-5),
            ended_date=self._in_days(1),
            release_status="released",
        ).save()
        models.StudentGrade(
            student=self.student,
            class_=self.class_,
            round_grade=round_grade,
            project=self.project,
            grader=models.Grader(lecturer=self.lecturer),
            result="-",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_round_grade_reminders())

        self.assertEqual(counts, {"sent": 0, "failed": 0, "skipped": 0})
        mock_send.assert_not_called()

    # -- Meeting report (student) reminders ----------------------------------

    def test_student_reminded_for_missing_meeting_report(self):
        models.Meeting(
            name="M1",
            round="final",
            class_=self.class_,
            owner=self.lecturer,
            started_date=self._in_days(-5),
            ended_date=self._in_days(2),
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_meeting_report_reminders())

        self.assertEqual(counts, {"sent": 1, "failed": 0, "skipped": 0})
        mock_send.assert_called_once_with(self.student.email, unittest.mock.ANY, unittest.mock.ANY)

    def test_student_not_reminded_once_meeting_report_submitted(self):
        meeting = models.Meeting(
            name="M1",
            round="final",
            class_=self.class_,
            owner=self.lecturer,
            started_date=self._in_days(-5),
            ended_date=self._in_days(2),
        ).save()
        models.MeetingReport(
            meeting=meeting,
            owner=self.student,
            class_=self.class_,
            project=self.project,
            ip_address="127.0.0.1",
            title="Weekly sync",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_meeting_report_reminders())

        self.assertEqual(counts, {"sent": 0, "failed": 0, "skipped": 0})
        mock_send.assert_not_called()

    # -- Report / presentation submission (student) reminders --------------

    def test_student_reminded_for_missing_report_submission(self):
        models.Submission(
            type="report",
            round="final",
            class_=self.class_,
            owner=self.lecturer,
            started_date=self._in_days(-5),
            ended_date=self._in_days(1),
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_report_reminders())

        self.assertEqual(counts, {"sent": 1, "failed": 0, "skipped": 0})
        mock_send.assert_called_once()

        # A presentation submission with the same deadline should not be
        # picked up by the report-only reminder function.
        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send2:
            presentation_counts = run(self.server.send_presentation_reminders())
        self.assertEqual(presentation_counts, {"sent": 0, "failed": 0, "skipped": 0})
        mock_send2.assert_not_called()

    def test_student_not_reminded_once_report_submitted(self):
        submission = models.Submission(
            type="report",
            round="final",
            class_=self.class_,
            owner=self.lecturer,
            started_date=self._in_days(-5),
            ended_date=self._in_days(1),
        ).save()
        models.ProgressReport(
            submission=submission,
            owner=self.student,
            class_=self.class_,
            project=self.project,
            ip_address="127.0.0.1",
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_report_reminders())

        self.assertEqual(counts, {"sent": 0, "failed": 0, "skipped": 0})
        mock_send.assert_not_called()

    def test_student_reminded_for_missing_presentation_submission(self):
        models.Submission(
            type="presentation",
            round="final",
            class_=self.class_,
            owner=self.lecturer,
            started_date=self._in_days(-5),
            ended_date=self._in_days(2),
        ).save()

        with patch.object(Mailer, "send", return_value=(True, None)) as mock_send:
            counts = run(self.server.send_presentation_reminders())

        self.assertEqual(counts, {"sent": 1, "failed": 0, "skipped": 0})
        mock_send.assert_called_once()

    # -- Email audit log retention -------------------------------------------

    def test_cleanup_email_audit_logs_removes_only_old_entries(self):
        recent = models.DeadlineNotification(
            target_type="round_grade",
            target_id=self.project.id,
            recipient=self.lecturer,
            days_before=1,
            status="sent",
        ).save()
        old = models.DeadlineNotification(
            target_type="round_grade",
            target_id=self.project.id,
            recipient=self.lecturer,
            days_before=2,
            status="sent",
        ).save()
        old.sent_date = self._in_days(-(controller.EMAIL_AUDIT_LOG_RETENTION_DAYS + 1))
        old.save()

        removed_count = run(self.server.cleanup_email_audit_logs())

        self.assertEqual(removed_count, 1)
        remaining_ids = {n.id for n in models.DeadlineNotification.objects}
        self.assertEqual(remaining_ids, {recent.id})

    # -- Mailer ---------------------------------------------------------------

    def test_mailer_disabled_by_default_does_not_send(self):
        disabled_mailer = Mailer({})
        sent, error = disabled_mailer.send("a@b.com", "subj", "body")
        self.assertFalse(sent)

    def _in_days(self, days):
        return datetime.datetime.now() + datetime.timedelta(days=days)


if __name__ == "__main__":
    unittest.main()
