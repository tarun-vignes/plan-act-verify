from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from multi_agent_builder.demo.app import DemoApplication


class DemoApplicationTests(unittest.TestCase):
    def test_home_page_renders_without_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DemoApplication(output_root=Path(temp_dir))
            response = app.handle("GET", "/")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Run the builder to populate this view.", response.body)

    def test_build_endpoint_generates_summary_and_artifact_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DemoApplication(output_root=Path(temp_dir))
            response = app.handle(
                "POST",
                "/api/build",
                json.dumps({"idea": "Inventory tracker for a small operations team"}).encode("utf-8"),
            )
            self.assertEqual(response.status_code, 202)
            payload = json.loads(response.body.decode("utf-8"))
            self.assertIn(payload["job"]["status"], {"queued", "running"})
            job_id = payload["job"]["job_id"]

            final_payload = None
            for _ in range(50):
                time.sleep(0.05)
                status_response = app.handle("GET", f"/api/builds/{job_id}")
                self.assertEqual(status_response.status_code, 200)
                candidate = json.loads(status_response.body.decode("utf-8"))
                if candidate["job"]["status"] == "completed":
                    final_payload = candidate
                    break

            self.assertIsNotNone(final_payload)
            assert final_payload is not None
            self.assertEqual(final_payload["summary"]["status"], "success")
            self.assertGreater(final_payload["job"]["event_count"], 0)
            latest = app.handle("GET", "/api/runs/latest")
            self.assertEqual(latest.status_code, 200)
            artifact = app.handle("GET", f"/runs/{final_payload['summary']['run_id']}/artifact/build_summary.md")
            self.assertEqual(artifact.status_code, 200)
            self.assertIn(b"Build Summary", artifact.body)

    def test_completed_job_persists_across_app_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DemoApplication(output_root=Path(temp_dir))
            response = app.handle(
                "POST",
                "/api/build",
                json.dumps({"idea": "Inventory tracker for a small operations team"}).encode("utf-8"),
            )
            job_id = json.loads(response.body.decode("utf-8"))["job"]["job_id"]

            for _ in range(50):
                time.sleep(0.05)
                payload = json.loads(app.handle("GET", f"/api/builds/{job_id}").body.decode("utf-8"))
                if payload["job"]["status"] == "completed":
                    break

            restarted = DemoApplication(output_root=Path(temp_dir))
            recovered = restarted.handle("GET", f"/api/builds/{job_id}")
            self.assertEqual(recovered.status_code, 200)
            recovered_payload = json.loads(recovered.body.decode("utf-8"))
            self.assertEqual(recovered_payload["job"]["status"], "completed")
            self.assertEqual(recovered_payload["summary"]["status"], "success")


if __name__ == "__main__":
    unittest.main()
