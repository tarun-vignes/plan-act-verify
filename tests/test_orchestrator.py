from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from multi_agent_builder.implementation.implementation_agent import ImplementationAgent
from multi_agent_builder.orchestration.orchestrator_agent import OrchestratorAgent
from multi_agent_builder.planning.architecture_agent import ArchitectureAgent
from multi_agent_builder.planning.specification_agent import SpecificationAgent
from multi_agent_builder.runtime.agent_backends import RecordingLLMBackend


class OrchestratorTests(unittest.TestCase):
    def test_end_to_end_build_generates_working_prototype(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = OrchestratorAgent(output_root=Path(temp_dir))
            result = orchestrator.execute("Inventory tracker for a small operations team")
            self.assertEqual(result.summary.status, "success")
            self.assertTrue(result.test_report.passed)
            self.assertTrue((result.run_dir / "artifacts" / "build_summary.json").exists())
            self.assertTrue((result.run_dir / "prototype" / "app" / "server.py").exists())
            self.assertEqual(result.summary.agent_backends["implementation"], "heuristic")
            self.assertEqual(len(result.implementation.worker_records), 3)

    def test_recording_backend_captures_agent_invocation(self) -> None:
        backend = RecordingLLMBackend()
        agent = SpecificationAgent(backend=backend)
        artifact = agent.run("Internal feedback board for developer platform teams")
        self.assertEqual(artifact.context.entity_collection_path, "feedback-items")
        self.assertEqual(len(backend.invocations), 1)
        self.assertEqual(backend.invocations[0].expected_output, "RequirementArtifact")

    def test_parallel_implementation_workers_report_owned_files(self) -> None:
        requirements = SpecificationAgent().run("Inventory tracker for a small operations team")
        architecture = ArchitectureAgent().run(requirements)
        with tempfile.TemporaryDirectory() as temp_dir:
            implementation = ImplementationAgent().run(Path(temp_dir), requirements, architecture)
            self.assertEqual(len(implementation.worker_records), 3)
            owned_files = {path for record in implementation.worker_records for path in record.generated_files}
            self.assertIn("app/server.py", owned_files)
            self.assertIn("README.md", owned_files)


if __name__ == "__main__":
    unittest.main()
