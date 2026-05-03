import unittest

from multi_agent.a2a.orchestrator import A2AOrchestrator
from multi_agent.a2a.protocol import TaskStatus


class TestA2AModes(unittest.TestCase):
    def test_sequential_mode(self):
        orch = A2AOrchestrator()
        result = orch.run_sequential("Design agent quality checks")
        self.assertEqual(result["mode"], "sequential")
        self.assertEqual(len(result["tasks"]), 2)
        self.assertTrue(all(t.status == TaskStatus.SUCCEEDED for t in result["tasks"]))

    def test_parallel_mode(self):
        orch = A2AOrchestrator()
        result = orch.run_parallel("calculate 8 * 8")
        self.assertEqual(result["mode"], "parallel")
        self.assertEqual(len(result["tasks"]), 2)

    def test_conditional_mode_math(self):
        orch = A2AOrchestrator()
        result = orch.run_conditional("calculate 9 + 1")
        self.assertEqual(result["chosen"], "math_agent")

    def test_pipeline_mode(self):
        orch = A2AOrchestrator()
        result = orch.run_pipeline("Create architecture checklist")
        self.assertEqual(result["mode"], "pipeline")
        self.assertEqual(len(result["tasks"]), 3)


if __name__ == "__main__":
    unittest.main()
