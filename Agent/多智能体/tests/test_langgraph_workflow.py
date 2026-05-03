import unittest

from multi_agent.langgraph_workflow import run_langgraph_demo


class TestLangGraphWorkflow(unittest.TestCase):
    def test_langgraph_math_route(self):
        result = run_langgraph_demo("calculate 3 + 5")
        self.assertEqual(result["route"], "math")
        self.assertIn("Math result:", result["primary_output"])
        self.assertIn("Confidence:", result["final_answer"])

    def test_langgraph_research_route(self):
        result = run_langgraph_demo("How to design reliable multi-agent system?")
        self.assertEqual(result["route"], "research")
        self.assertIn("Research summary:", result["primary_output"])


if __name__ == "__main__":
    unittest.main()
