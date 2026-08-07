import unittest
from bussaya import models


class RubricCriterionLevelTest(unittest.TestCase):
    def test_rubric_criterion_level_explanations(self):
        levels_data = {
            "A": "Excellent work, exceeds all expectations",
            "B+": "Very good work, exceeds most expectations",
            "B": "Good work, meets all major requirements",
            "C+": "Above average work, minor flaws",
            "C": "Satisfactory work, meets minimum standards",
            "D+": "Below average work, missing some key elements",
            "D": "Poor work, barely passing",
            "E": "Failing work, insufficient evidence",
            "I": "Incomplete work",
            "W": "Withdrawn",
        }

        level_explanations = [
            models.RubricLevelExplanation(level=lvl, explanation=exp)
            for lvl, exp in levels_data.items()
        ]

        criterion = models.RubricCriterion(
            name="Presentation Quality",
            description="Evaluates content structure and delivery",
            max_score=40,
            level_explanations=level_explanations,
        )

        self.assertEqual(criterion.max_score, 40)
        # Check retrieving each level's explanation
        for lvl, exp in levels_data.items():
            self.assertEqual(criterion.get_level_explanation(lvl), exp)

        self.assertEqual(criterion.get_level_explanations_dict(), levels_data)

    def test_rubric_criterion_snapshot_level_explanations(self):
        levels_data = {
            "A": "A level exp",
            "B+": "B+ level exp",
            "B": "B level exp",
            "C+": "C+ level exp",
            "C": "C level exp",
            "D+": "D+ level exp",
            "D": "D level exp",
            "E": "E level exp",
            "I": "I level exp",
            "W": "W level exp",
        }

        level_explanations = [
            models.RubricLevelExplanation(level=lvl, explanation=exp)
            for lvl, exp in levels_data.items()
        ]

        snapshot = models.RubricCriterionSnapshot(
            name="System Design",
            description="Architecture and diagrams",
            max_score=60,
            level_explanations=level_explanations,
        )

        self.assertEqual(snapshot.max_score, 60)
        for lvl, exp in levels_data.items():
            self.assertEqual(snapshot.get_level_explanation(lvl), exp)

        self.assertEqual(snapshot.get_level_explanations_dict(), levels_data)

    def test_rubric_total_max_score_summation(self):
        c1 = models.RubricCriterion(name="Part 1", max_score=40)
        c2 = models.RubricCriterion(name="Part 2", max_score=60)
        template = models.RubricTemplate(name="Project Evaluation", criteria=[c1, c2])
        self.assertEqual(template.get_total_max_score(), 100)

    def test_rubric_score_calculation(self):
        c1 = models.RubricCriterionSnapshot(name="Part 1", max_score=40)
        c2 = models.RubricCriterionSnapshot(name="Part 2", max_score=60)
        round_rubric = models.RoundGradeRubric(criteria=[c1, c2])

        cs1 = models.CriterionScore(criterion_id=c1.id, score=40)  # A (100% = 40)
        cs2 = models.CriterionScore(criterion_id=c2.id, score=45)  # B (75% = 45)
        score_doc = models.RubricScore(round_grade_rubric=round_rubric, criterion_scores=[cs1, cs2])

        self.assertEqual(score_doc.get_percentage(), 85.0)  # (40 + 45) / 100 * 100 = 85%
        self.assertEqual(score_doc.get_point(), 3.4)  # 85% * 4.0 / 100 = 3.4
        user = models.User()
        self.assertEqual(user.get_point_to_grade(score_doc.get_point()), "B+")

    def test_rubric_grade_levels_constant(self):
        expected_levels = ["A", "B+", "B", "C+", "C", "D+", "D", "E", "I", "W"]
        self.assertEqual(models.RUBRIC_GRADE_LEVELS, expected_levels)
