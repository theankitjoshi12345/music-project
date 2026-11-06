import base64
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


SETTINGS = {
    "GOOGLE_CLOUD_PROJECT": "music-companion-513717",
    "EXPECTED_BUDGET_ID": "9f6f514b-5508-441c-ba32-249b32edf00f",
    "EXPECTED_BILLING_ACCOUNT_ID": "01124F-AA2E30-D8B14D",
    "EXPECTED_BUDGET_DISPLAY_NAME": "Music Companion zero-cost guard",
    "EXPECTED_BUDGET_AMOUNT_USD": "1.00",
}


def notification(*, cost=1.0, threshold=1.0, budget_id=None, display_name=None):
    payload = {
        "budgetDisplayName": display_name or SETTINGS["EXPECTED_BUDGET_DISPLAY_NAME"],
        "alertThresholdExceeded": threshold,
        "costAmount": cost,
        "costIntervalStart": "2026-11-01T00:00:00Z",
        "budgetAmount": 1.0,
        "budgetAmountType": "SPECIFIED_AMOUNT",
        "currencyCode": "USD",
    }
    return {
        "message": {
            "attributes": {
                "billingAccountId": SETTINGS["EXPECTED_BILLING_ACCOUNT_ID"],
                "budgetId": budget_id or SETTINGS["EXPECTED_BUDGET_ID"],
                "schemaVersion": "1.0",
            },
            "data": base64.b64encode(json.dumps(payload).encode()).decode(),
        },
        "subscription": "projects/music-companion-513717/subscriptions/cost-guard",
    }


class CostGuardTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, SETTINGS, clear=False)
        environment.start()
        self.addCleanup(environment.stop)
        from app import app

        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_health(self):
        self.assertEqual(self.client.get("/healthz").get_json(), {"status": "ok"})

    def test_rejects_malformed_message(self):
        response = self.client.post("/", json={"message": {"data": "not-base64"}})
        self.assertEqual(response.status_code, 400)

    def test_rejects_wrong_budget(self):
        response = self.client.post("/", json=notification(budget_id="other"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["reason"], "Unexpected budget")

    @patch("app._billing_client")
    def test_below_threshold_does_not_call_billing(self, client_factory):
        response = self.client.post("/", json=notification(cost=0.5, threshold=0.5))
        self.assertEqual(response.status_code, 204)
        client_factory.assert_not_called()

    @patch("app._billing_client")
    def test_threshold_unlinks_billing(self, client_factory):
        client = Mock()
        client.get_project_billing_info.return_value = SimpleNamespace(billing_enabled=True)
        client_factory.return_value = client

        response = self.client.post("/", json=notification())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "disabled"})
        client.update_project_billing_info.assert_called_once()
        call = client.update_project_billing_info.call_args.kwargs
        self.assertEqual(call["name"], "projects/music-companion-513717")
        self.assertEqual(call["project_billing_info"].billing_account_name, "")

    @patch("app._billing_client")
    def test_duplicate_notification_is_idempotent(self, client_factory):
        client = Mock()
        client.get_project_billing_info.return_value = SimpleNamespace(billing_enabled=False)
        client_factory.return_value = client

        response = self.client.post("/", json=notification(cost=2.0))

        self.assertEqual(response.get_json(), {"status": "already-disabled"})
        client.update_project_billing_info.assert_not_called()

    @patch("app._billing_client")
    def test_api_failure_requests_pubsub_retry(self, client_factory):
        client_factory.side_effect = RuntimeError("temporary failure")
        response = self.client.post("/", json=notification())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"status": "retry"})


if __name__ == "__main__":
    unittest.main()
