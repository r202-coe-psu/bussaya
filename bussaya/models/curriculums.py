import mongoengine as me
import datetime


class Curriculum(me.Document):
    meta = {"collection": "curriculums"}

    name = me.StringField(required=True, max_length=255)
    name_th = me.StringField(max_length=255, default="")
    code = me.StringField(max_length=100)

    status = me.StringField(required=True, default="active")

    creator = me.ReferenceField("User", dbref=True)
    last_updated_by = me.ReferenceField("User", dbref=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    def get_plos(self):
        return PLO.objects(curriculum=self, status="active").order_by("order")

    def get_clos(self):
        return CLO.objects(curriculum=self, status="active").order_by("order")

    def get_plo_achievement_by_class_type(self):
        """For each active PLO in this curriculum, average the achievement
        percentage (rolled up from graded rubric criteria via their CLOs, or
        a criterion's own direct PLO links) separately per class type, so an
        admin can compare how a curriculum's outcomes are demonstrated
        across preproject/project/cooperative/etc. classes that share it."""

        from .classes import Class, TYPE_CHOICE
        from .grades import StudentGrade

        scores_by_type = {}  # class_type -> plo_id -> list of percentages
        for class_ in Class.objects(curriculums=self):
            for student_grade in StudentGrade.objects(class_=class_):
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
                        if not plo.curriculum or plo.curriculum.id != self.id:
                            continue
                        bucket = scores_by_type.setdefault(class_.type, {})
                        bucket.setdefault(plo.id, []).append(percentage)

        class_types = list(TYPE_CHOICE)
        rows = []
        for plo in self.get_plos():
            by_class_type = {}
            for class_type, _ in class_types:
                percentages = scores_by_type.get(class_type, {}).get(plo.id)
                if percentages:
                    by_class_type[class_type] = {
                        "percentage": sum(percentages) / len(percentages),
                        "student_count": len(percentages),
                    }
                else:
                    by_class_type[class_type] = None
            rows.append({"plo": plo, "by_class_type": by_class_type})

        return {"class_types": class_types, "rows": rows}


class PLO(me.Document):
    meta = {"collection": "plos"}

    curriculum = me.ReferenceField("Curriculum", dbref=True, required=True)

    code = me.StringField(required=True, max_length=50)
    description = me.StringField(required=True)
    description_th = me.StringField(default="")
    order = me.IntField(default=0)

    status = me.StringField(required=True, default="active")

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    def get_label(self):
        curriculum_code = self.curriculum.code if self.curriculum else ""
        return f"[{curriculum_code}] {self.code} - {self.description}"


class CLO(me.Document):
    meta = {"collection": "clos"}

    curriculum = me.ReferenceField("Curriculum", dbref=True, required=True)
    plos = me.ListField(me.ReferenceField("PLO", dbref=True))

    code = me.StringField(required=True, max_length=50)
    description = me.StringField(required=True)
    description_th = me.StringField(default="")
    order = me.IntField(default=0)

    status = me.StringField(required=True, default="active")

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    # flask_mongoengine's model_form looks up "{field_name}_label_modifier" on the
    # model to label options of a ListField(ReferenceField(...)) - field_args
    # label_modifier is ignored for that field type.
    plos_label_modifier = staticmethod(lambda plo: plo.get_label())

    def get_label(self):
        curriculum_code = self.curriculum.code if self.curriculum else ""
        return f"[{curriculum_code}] {self.code} - {self.description}"
