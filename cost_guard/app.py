"""Private Cloud Run endpoint that unlinks billing at the approved budget.

Cloud Run performs caller authentication for the authenticated Pub/Sub push
subscription. This module additionally validates the exact billing account,
budget, schema, currency, and threshold before changing billing state.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
from decimal import Decimal, InvalidOperation
from typing import Any

from flask import Flask, jsonify, request
from google.cloud import billing_v1


app = Flask(__name__)


class InvalidNotification(ValueError):
    """Raised when a request is not the configured budget notification."""


def _required_setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required setting: {name}")
    return value


def _decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise InvalidNotification(f"Invalid {field}") from error
    if not number.is_finite() or number < 0:
        raise InvalidNotification(f"Invalid {field}")
    return number


def _parse_notification(envelope: Any) -> tuple[dict[str, Any], dict[str, str]]:
    if not isinstance(envelope, dict) or not isinstance(envelope.get("message"), dict):
        raise InvalidNotification("Missing Pub/Sub message")
    message = envelope["message"]
    attributes = message.get("attributes")
    if not isinstance(attributes, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in attributes.items()
    ):
        raise InvalidNotification("Invalid Pub/Sub attributes")
    encoded = message.get("data")
    if not isinstance(encoded, str):
        raise InvalidNotification("Missing Pub/Sub data")
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        payload = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidNotification("Invalid Pub/Sub data") from error
    if not isinstance(payload, dict):
        raise InvalidNotification("Invalid budget payload")
    return payload, attributes


def _validate_notification(payload: dict[str, Any], attributes: dict[str, str]) -> bool:
    expected_budget_id = _required_setting("EXPECTED_BUDGET_ID")
    expected_billing_account = _required_setting("EXPECTED_BILLING_ACCOUNT_ID")
    expected_display_name = _required_setting("EXPECTED_BUDGET_DISPLAY_NAME")
    expected_amount = _decimal(_required_setting("EXPECTED_BUDGET_AMOUNT_USD"), "configured amount")

    if attributes.get("schemaVersion") != "1.0":
        raise InvalidNotification("Unexpected schema version")
    if attributes.get("budgetId") != expected_budget_id:
        raise InvalidNotification("Unexpected budget")
    if attributes.get("billingAccountId") != expected_billing_account:
        raise InvalidNotification("Unexpected billing account")
    if payload.get("budgetDisplayName") != expected_display_name:
        raise InvalidNotification("Unexpected budget display name")
    if payload.get("currencyCode") != "USD":
        raise InvalidNotification("Unexpected currency")
    if payload.get("budgetAmountType") != "SPECIFIED_AMOUNT":
        raise InvalidNotification("Unexpected budget amount type")

    budget_amount = _decimal(payload.get("budgetAmount"), "budgetAmount")
    cost_amount = _decimal(payload.get("costAmount"), "costAmount")
    if budget_amount != expected_amount:
        raise InvalidNotification("Unexpected budget amount")

    threshold = payload.get("alertThresholdExceeded")
    if threshold is None:
        return False
    threshold_amount = _decimal(threshold, "alertThresholdExceeded")
    return threshold_amount >= Decimal("1") and cost_amount >= budget_amount


def _billing_client() -> billing_v1.CloudBillingClient:
    return billing_v1.CloudBillingClient()


@app.get("/healthz")
def health() -> tuple[Any, int]:
    return jsonify({"status": "ok"}), 200


@app.post("/")
def budget_notification() -> tuple[Any, int]:
    try:
        payload, attributes = _parse_notification(request.get_json(silent=True))
        threshold_reached = _validate_notification(payload, attributes)
    except InvalidNotification as error:
        return jsonify({"status": "rejected", "reason": str(error)}), 400
    except RuntimeError as error:
        app.logger.error("Cost guard configuration error: %s", error)
        return jsonify({"status": "misconfigured"}), 500

    if not threshold_reached:
        return jsonify({"status": "below-threshold"}), 204

    project_name = f"projects/{_required_setting('GOOGLE_CLOUD_PROJECT')}"
    try:
        client = _billing_client()
        billing_info = client.get_project_billing_info(name=project_name)
        if not billing_info.billing_enabled:
            return jsonify({"status": "already-disabled"}), 200
        client.update_project_billing_info(
            name=project_name,
            project_billing_info=billing_v1.ProjectBillingInfo(
                billing_account_name=""
            ),
        )
    except Exception:
        # Returning a failure makes Pub/Sub retry instead of silently losing
        # the shutdown request. Cloud Logging receives the stack trace.
        app.logger.exception("Failed to disable project billing")
        return jsonify({"status": "retry"}), 500

    app.logger.critical("Billing disabled after the verified budget reached 100%%")
    return jsonify({"status": "disabled"}), 200

