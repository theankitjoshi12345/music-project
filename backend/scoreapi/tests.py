from rest_framework.test import APITestCase

from .models import Passage, PracticeMark, Score


class ScoreApiTests(APITestCase):
    def setUp(self):
        self.score = Score.objects.create(
            title="Symphony No. 1",
            movement="Movement I",
            instrument="Percussion",
            page_count=4,
            available_offline=True,
        )
        self.other_score = Score.objects.create(
            title="Symphony No. 1",
            movement="Movement II",
            instrument="Percussion",
            page_count=4,
            available_offline=True,
        )
        self.passage = Passage.objects.create(
            score=self.score, section="B", measure_number=24, page_number=2
        )
        self.other_passage = Passage.objects.create(
            score=self.other_score, section="A", measure_number=1, page_number=1
        )

    def test_health_check_is_preserved(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_score_list_and_detail_include_library_context(self):
        response = self.client.get("/api/scores/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        first_score = next(item for item in response.json() if item["id"] == self.score.id)
        self.assertEqual(first_score["passage_count"], 1)
        self.assertTrue(first_score["available_offline"])

        detail = self.client.get(f"/api/scores/{self.score.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["movement"], "Movement I")

    def test_passages_are_limited_to_the_requested_score(self):
        response = self.client.get(f"/api/scores/{self.score.id}/passages/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [
            {
                "id": self.passage.id,
                "section": "B",
                "measure_number": 24,
                "page_number": 2,
                "is_marked_for_practice": False,
            }
        ])

    def test_create_mark_and_filter_unresolved_marks(self):
        response = self.client.post(
            "/api/practice-marks/",
            {"passage_id": self.passage.id, "note": " Keep the rhythm even. "},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["note"], "Keep the rhythm even.")
        self.assertFalse(response.json()["is_resolved"])
        self.assertEqual(response.json()["passage"]["measure_number"], 24)

        listing = self.client.get(
            f"/api/practice-marks/?score={self.score.id}&status=unresolved"
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()), 1)

    def test_duplicate_mark_and_invalid_status_are_rejected(self):
        PracticeMark.objects.create(passage=self.passage)
        duplicate = self.client.post(
            "/api/practice-marks/",
            {"passage_id": self.passage.id},
            format="json",
        )
        invalid_status = self.client.get("/api/practice-marks/?status=pending")

        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("passage_id", duplicate.json())
        self.assertEqual(invalid_status.status_code, 400)
        self.assertEqual(invalid_status.json(), {
            "status": "Use 'unresolved' or 'resolved'."
        })

    def test_patch_updates_note_and_resolution_without_moving_passage(self):
        mark = PracticeMark.objects.create(passage=self.passage)
        response = self.client.patch(
            f"/api/practice-marks/{mark.id}/",
            {"note": "Review transition", "is_resolved": True},
            format="json",
        )
        move_attempt = self.client.patch(
            f"/api/practice-marks/{mark.id}/",
            {"passage_id": self.other_passage.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["note"], "Review transition")
        self.assertTrue(response.json()["is_resolved"])
        self.assertEqual(move_attempt.status_code, 400)
        self.assertIn("passage_id", move_attempt.json())
