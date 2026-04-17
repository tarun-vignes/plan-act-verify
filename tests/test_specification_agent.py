from __future__ import annotations

import unittest

from multi_agent_builder.planning.specification_agent import SpecificationAgent


class SpecificationAgentTests(unittest.TestCase):
    def test_generates_contracts_and_requirement_gaps(self) -> None:
        agent = SpecificationAgent()
        artifact = agent.run("Internal feedback board for developer platform teams")
        self.assertGreaterEqual(len(artifact.api_contracts), 4)
        self.assertIn("Authentication and authorization model", artifact.missing_requirements)
        self.assertEqual(artifact.context.entity_collection_path, "feedback-items")


if __name__ == "__main__":
    unittest.main()

