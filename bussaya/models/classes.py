import mongoengine as me
import datetime

from . import users
from . import projects

TYPE_CHOICE = [
    ("preproject", "Preproject"),
    ("project", "Project"),
    ("cooperative", "Cooperative Education"),
    ("precooperative", "Pre-cooperative Education"),
    ("thesis", "Thesis"),
]


class Class(me.Document):
    meta = {"collection": "classes"}

    name = me.StringField(required=True, max_length=255)
    description = me.StringField()
    code = me.StringField(max_length=100)
    student_ids = me.ListField(me.StringField())

    tags = me.ListField(me.StringField(required=True))
    type = me.StringField(choices=TYPE_CHOICE)
    curriculums = me.ListField(me.ReferenceField("Curriculum", dbref=True))

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    started_date = me.DateField(required=True, default=datetime.datetime.today)
    ended_date = me.DateField(required=True, default=datetime.datetime.today)

    owner = me.ReferenceField("User", dbref=True, required=True)

    def get_students(self):
        return users.User.objects(username__in=self.student_ids).order_by("username")

    def get_projects_by_advisors(self, *args):
        return projects.Project.objects(advisors__in=args)

    def get_projects(self):
        students = self.get_students()
        return projects.Project.objects(
            me.Q(creator__in=students) | me.Q(students__in=students)
        ).order_by("name")

    def is_available_project(self, project):
        for student in project.students:
            if str(student.username) not in self.student_ids:
                return False
        return True

    def get_advisees_by_advisors(self, *args):
        students = self.get_students()
        # adv_projects = projects.Project.objects(advisor__in=args, students__in=students)
        adv_projects = projects.Project.objects(advisors=args, students__in=students)
        return [s for project in adv_projects for s in project.students]

    def is_in_time(self):
        return self.started_date <= datetime.datetime.now().date() <= self.ended_date

    def count_grade(self, round_grade):
        student_ids = self.student_ids

        grades = {
            "A": [0, []],
            "B+": [0, []],
            "B": [0, []],
            "C+": [0, []],
            "C": [0, []],
            "D+": [0, []],
            "D": [0, []],
            "E": [0, []],
            "I": [0, []],
            "W": [0, []],
        }

        for i in student_ids:
            user = users.User.objects.get(username=i)

            grade, caused = users.User.get_actual_grade(
                self=user, round_grade=round_grade
            )

            if grade in grades:
                grades[grade][0] += 1
                grades[grade][1].append(user)
            else:
                grades[grade] = [1, [user]]

        return grades

    def get_plo_achievement(self, pass_threshold=60):
        """For each PLO demonstrated by this class's graded rubric criteria,
        bucket every enrolled student's own average achievement percentage
        into "pass" (>= pass_threshold%) or "improvement" (< pass_threshold%).

        Only counts a student's percentage toward a PLO if the student's own
        curriculum matches that PLO's curriculum, mirroring
        Curriculum.get_plo_achievement_by_class_type()."""

        from .grades import StudentGrade

        plo_data = {}  # plo.id -> {"plo": plo, "students": {student.id: [percentage, ...]}}

        for student in self.get_students():
            if not student.curriculum:
                continue

            for student_grade in StudentGrade.objects(student=student, class_=self):
                rubric_score = student_grade.get_rubric_score()
                if not rubric_score:
                    continue

                for criterion in rubric_score.round_grade_rubric.get_sorted_criteria():
                    criterion_score = rubric_score.get_score_for(criterion.id)
                    if not criterion_score or criterion_score.score is None:
                        continue
                    if not criterion.max_score:
                        continue

                    percentage = (criterion_score.score / criterion.max_score) * 100

                    plos = set(criterion.plos)
                    for clo in criterion.clos:
                        plos.update(clo.plos)

                    for plo in plos:
                        if not plo.curriculum or plo.curriculum.id != student.curriculum.id:
                            continue
                        entry = plo_data.setdefault(plo.id, {"plo": plo, "students": {}})
                        entry["students"].setdefault(student.id, {
                            "student": student,
                            "percentages": [],
                        })
                        entry["students"][student.id]["percentages"].append(percentage)

        rows = []
        for data in plo_data.values():
            pass_students = []
            improvement_students = []
            for info in data["students"].values():
                percentage = sum(info["percentages"]) / len(info["percentages"])
                bucket = pass_students if percentage >= pass_threshold else improvement_students
                bucket.append({"student": info["student"], "percentage": percentage})

            pass_students.sort(key=lambda s: s["student"].username)
            improvement_students.sort(key=lambda s: s["student"].username)

            rows.append({
                "plo": data["plo"],
                "pass_students": pass_students,
                "improvement_students": improvement_students,
                "pass_count": len(pass_students),
                "improvement_count": len(improvement_students),
            })

        rows.sort(key=lambda row: row["plo"].code)
        return rows
