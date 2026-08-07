import mongoengine as me
import datetime

from bson.objectid import ObjectId

from .classes import TYPE_CHOICE

RUBRIC_STATUS_CHOICES = ["draft", "active", "archived"]
RUBRIC_GRADE_LEVELS = ["A", "B+", "B", "C+", "C", "D+", "D", "E", "I", "W"]


class RubricLevelExplanation(me.EmbeddedDocument):
    level = me.StringField(required=True)
    explanation = me.StringField(default="")


class RubricCriterion(me.EmbeddedDocument):
    id = me.ObjectIdField(required=True, default=ObjectId)

    name = me.StringField(required=True, max_length=255)
    description = me.StringField(default="")
    max_score = me.FloatField(required=True, default=0)
    plos = me.ListField(me.ReferenceField("PLO", dbref=True))
    clos = me.ListField(me.ReferenceField("CLO", dbref=True))
    order = me.IntField(default=0)
    level_explanations = me.EmbeddedDocumentListField(RubricLevelExplanation)

    def get_level_explanation(self, level_name):
        for le in self.level_explanations:
            if le.level == level_name:
                return le.explanation
        return ""

    def get_level_explanations_dict(self):
        return {le.level: le.explanation for le in self.level_explanations}


class RubricTemplate(me.Document):
    meta = {"collection": "rubric_templates"}

    name = me.StringField(required=True, max_length=255)
    curriculums = me.ListField(
        me.ReferenceField("Curriculum", dbref=True), required=True
    )
    class_type = me.StringField(required=True, choices=TYPE_CHOICE)
    description = me.StringField(default="")

    status = me.StringField(
        required=True, default="draft", choices=RUBRIC_STATUS_CHOICES
    )

    criteria = me.EmbeddedDocumentListField(RubricCriterion)

    version = me.IntField(default=1)
    cloned_from = me.ReferenceField("self", dbref=True)

    creator = me.ReferenceField("User", dbref=True)
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    def is_editable(self):
        return True

    def get_total_max_score(self):
        return sum(c.max_score for c in self.criteria)

    def get_sorted_criteria(self):
        return sorted(self.criteria, key=lambda c: c.order)

    def activate(self):
        RubricTemplate.objects(
            curriculums__in=self.curriculums,
            class_type=self.class_type,
            status="active",
            id__ne=self.id,
        ).update(set__status="archived")
        self.status = "active"
        self.save()

    def archive(self):
        self.status = "archived"
        self.save()

    def clone(self, creator=None):
        clone = RubricTemplate(
            name=self.name,
            curriculums=list(self.curriculums),
            class_type=self.class_type,
            description=self.description,
            status="draft",
            version=self.version + 1,
            cloned_from=self,
            creator=creator or self.creator,
        )
        for criterion in self.criteria:
            level_exps = [
                RubricLevelExplanation(level=le.level, explanation=le.explanation)
                for le in criterion.level_explanations
            ]
            clone.criteria.append(
                RubricCriterion(
                    name=criterion.name,
                    description=criterion.description,
                    max_score=criterion.max_score,
                    plos=criterion.plos,
                    clos=criterion.clos,
                    order=criterion.order,
                    level_explanations=level_exps,
                )
            )
        clone.save()
        return clone

    @classmethod
    def get_active(cls, curriculum, class_type):
        return cls.objects(
            curriculums=curriculum, class_type=class_type, status="active"
        ).first()


class RubricCriterionSnapshot(me.EmbeddedDocument):
    id = me.ObjectIdField(required=True, default=ObjectId)

    name = me.StringField(required=True, max_length=255)
    description = me.StringField(default="")
    max_score = me.FloatField(required=True, default=0)
    plos = me.ListField(me.ReferenceField("PLO", dbref=True))
    clos = me.ListField(me.ReferenceField("CLO", dbref=True))
    order = me.IntField(default=0)
    level_explanations = me.EmbeddedDocumentListField(RubricLevelExplanation)

    def get_level_explanation(self, level_name):
        for le in self.level_explanations:
            if le.level == level_name:
                return le.explanation
        return ""

    def get_level_explanations_dict(self):
        return {le.level: le.explanation for le in self.level_explanations}


class RoundGradeRubric(me.Document):
    meta = {"collection": "round_grade_rubrics"}

    round_grade = me.ReferenceField("RoundGrade", dbref=True, required=True, unique=True)
    template = me.ReferenceField("RubricTemplate", dbref=True, required=True)
    criteria = me.EmbeddedDocumentListField(RubricCriterionSnapshot)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    def get_sorted_criteria(self):
        return sorted(self.criteria, key=lambda c: c.order)

    def get_total_max_score(self):
        return sum(c.max_score for c in self.criteria)

    def get_criterion(self, criterion_id):
        for criterion in self.criteria:
            if str(criterion.id) == str(criterion_id):
                return criterion
        return None


def get_or_create_round_grade_rubric(round_grade):
    """Lazily snapshot the active RubricTemplate for round_grade.class_.type
    into a RoundGradeRubric, mirroring check_and_create_student_grade_profile's
    lazy-creation pattern. Returns None if no active template exists yet."""

    existing = RoundGradeRubric.objects(round_grade=round_grade).first()
    if existing:
        return existing

    class_ = round_grade.class_
    if not class_.curriculum:
        return None

    template = RubricTemplate.get_active(class_.curriculum, class_.type)
    if not template:
        return None

    round_grade_rubric = RoundGradeRubric(round_grade=round_grade, template=template)
    for criterion in template.get_sorted_criteria():
        level_exps = [
            RubricLevelExplanation(level=le.level, explanation=le.explanation)
            for le in criterion.level_explanations
        ]
        round_grade_rubric.criteria.append(
            RubricCriterionSnapshot(
                name=criterion.name,
                description=criterion.description,
                max_score=criterion.max_score,
                plos=criterion.plos,
                clos=criterion.clos,
                order=criterion.order,
                level_explanations=level_exps,
            )
        )
    round_grade_rubric.save()
    return round_grade_rubric


class CriterionScore(me.EmbeddedDocument):
    criterion_id = me.ObjectIdField(required=True)
    score = me.FloatField()
    comment = me.StringField(default="")


class RubricScore(me.Document):
    meta = {"collection": "rubric_scores"}

    student_grade = me.ReferenceField(
        "StudentGrade", dbref=True, required=True, unique=True
    )
    round_grade_rubric = me.ReferenceField("RoundGradeRubric", dbref=True, required=True)
    criterion_scores = me.EmbeddedDocumentListField(CriterionScore)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    def get_score_for(self, criterion_id):
        for criterion_score in self.criterion_scores:
            if str(criterion_score.criterion_id) == str(criterion_id):
                return criterion_score
        return None

    def is_complete(self):
        if not self.criterion_scores:
            return False
        return all(cs.score is not None for cs in self.criterion_scores)

    def get_percentage(self):
        scored = [cs for cs in self.criterion_scores if cs.score is not None]
        if not scored:
            return None

        criteria_by_id = {
            str(c.id): c for c in self.round_grade_rubric.criteria
        }
        total_score = 0
        total_max = 0
        for cs in scored:
            criterion = criteria_by_id.get(str(cs.criterion_id))
            if not criterion:
                continue
            total_score += cs.score
            total_max += criterion.max_score

        if total_max == 0:
            return None

        return (total_score / total_max) * 100

    def get_point(self):
        percentage = self.get_percentage()
        if percentage is None:
            return None
        return (percentage / 100) * 4.0
