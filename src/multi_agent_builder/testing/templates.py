from __future__ import annotations

import json

from ..models import RequirementArtifact


def _sample_payload(requirements: RequirementArtifact) -> str:
    payload: dict[str, object] = {}
    for index, field in enumerate(requirements.context.field_definitions, start=1):
        if field.field_type == "int":
            payload[field.name] = index * 5
        else:
            payload[field.name] = f"{field.name.replace('_', ' ')} sample"
    return json.dumps(payload, indent=8)


def render_test_files(requirements: RequirementArtifact) -> dict[str, str]:
    context = requirements.context
    payload = _sample_payload(requirements)
    missing_field = context.field_definitions[0].name
    service_test = f'''from __future__ import annotations

import unittest

from app.models import ValidationError
from app.service import PrototypeService


SAMPLE_PAYLOAD = {payload}


class PrototypeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PrototypeService()

    def test_create_record_persists_payload(self) -> None:
        record = self.service.create_record(dict(SAMPLE_PAYLOAD))
        self.assertTrue(record.id)
        self.assertEqual(record.payload["{missing_field}"], SAMPLE_PAYLOAD["{missing_field}"])

    def test_create_record_rejects_missing_required_field(self) -> None:
        payload = dict(SAMPLE_PAYLOAD)
        payload.pop("{missing_field}")
        with self.assertRaises(ValidationError):
            self.service.create_record(payload)

    def test_get_record_returns_none_for_unknown_id(self) -> None:
        self.assertIsNone(self.service.get_record("missing-id"))


if __name__ == "__main__":
    unittest.main()
'''
    api_test = f'''from __future__ import annotations

import unittest

from app.api import ApiRouter


SAMPLE_PAYLOAD = {payload}


class ApiRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = ApiRouter()

    def test_health_endpoint(self) -> None:
        response = self.router.handle("GET", "/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["status"], "ok")

    def test_metadata_endpoint(self) -> None:
        response = self.router.handle("GET", "/metadata")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["entity_collection"], "{context.entity_collection_path}")

    def test_create_then_list_round_trip(self) -> None:
        create_response = self.router.handle(
            "POST",
            "/{context.entity_collection_path}",
            dict(SAMPLE_PAYLOAD),
        )
        self.assertEqual(create_response.status_code, 201)
        list_response = self.router.handle("GET", "/{context.entity_collection_path}")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.body["count"], 1)


if __name__ == "__main__":
    unittest.main()
'''
    return {
        "tests/test_service.py": service_test,
        "tests/test_api.py": api_test,
    }

