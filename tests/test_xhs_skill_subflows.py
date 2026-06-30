import json
import unittest

from cozepy import grok_image_node as grok_module
from cozepy import openai_text_node as openai_module
from cozepy.graph import main_graph


def base_input(execute_model_calls=False):
    return {
        "grok_api_key": "gsk_test_secret_123456789",
        "openai_api_key": "sk-test_secret_123456789",
        "niche": "AI 副业",
        "audience": "想用 AI 做副业但没方向的上班族",
        "goal": "生成一组小红书图文卡片",
        "benchmark_notes": ["标题常用普通人也能做，正文是步骤清单和案例截图"],
        "comment_notes": ["我没有编程基础可以做吗", "有没有适合下班后做的项目", "能不能给一个从0开始的步骤"],
        "topic_research_notes": ["对标标题 1.8 万浏览，评论集中问零基础和下班后怎么做"],
        "constraints": ["不要承诺收益", "强调先验证需求"],
        "reference_image_notes": ["圆润线条", "明亮色板", "统一主角"],
        "card_count": 6,
        "image_count": 6,
        "execute_model_calls": execute_model_calls,
        "skill_flow_overrides": {
            "openai_text_skill": {
                "mode": "ultra_high",
                "steps": {
                    "generate_xhs_text": {
                        "prompt": "运营改写OpenAI子流程：用复盘口吻生成标题、脚本、正文和视觉brief。"
                    },
                    "review_text_for_image": {
                        "enabled": "false",
                    },
                },
            },
            "grok_image_skill": {
                "steps": {
                    "compose_page_prompts": {
                        "prompt": "运营改写Grok子流程：3:4卡通套图，统一角色，每页一个动作。"
                    }
                }
            },
        },
    }


class XhsSkillSubflowTests(unittest.TestCase):
    def test_skill_subflows_are_visible_editable_and_overrideable(self):
        result = main_graph.invoke(base_input())

        self.assertEqual(
            [flow["skill_key"] for flow in result["skill_subflows"]],
            ["openai_text_skill", "grok_image_skill"],
        )
        self.assertEqual(len(result["workflow_steps"]), 8)
        self.assertIn("skill_subflows", [step["node_key"] for step in result["workflow_steps"]])
        step_status = {step["node_key"]: step["status"] for step in result["workflow_steps"]}
        self.assertEqual(step_status["openai_text"], "parallel_branch")
        self.assertEqual(step_status["grok_image_set"], "parallel_branch")
        self.assertEqual(step_status["finalize"], "join")

        openai_steps = {step["step_key"]: step for step in result["skill_subflows"][0]["steps"]}
        grok_steps = {step["step_key"]: step for step in result["skill_subflows"][1]["steps"]}
        self.assertIn("运营改写OpenAI子流程", openai_steps["generate_xhs_text"]["final_prompt"])
        self.assertFalse(openai_steps["review_text_for_image"]["enabled"])
        self.assertIn("运营改写Grok子流程", grok_steps["compose_page_prompts"]["final_prompt"])

        prompt_keys = {prompt["key"] for prompt in result["editable_prompts"]}
        self.assertIn("openai_text_skill.generate_xhs_text", prompt_keys)
        self.assertIn("grok_image_skill.compose_page_prompts", prompt_keys)
        self.assertEqual(len(result["editable_prompts"]), 10)

    def test_workflow_diagram_has_parallel_branches_and_operator_panels(self):
        result = main_graph.invoke(base_input())

        edges = {
            (edge["from_node"], edge["to_node"]): edge["edge_type"]
            for edge in result["workflow_diagram_edges"]
        }
        self.assertEqual(edges[("prompt_editor", "openai_text")], "parallel")
        self.assertEqual(edges[("prompt_editor", "grok_image_set")], "parallel")
        self.assertEqual(edges[("openai_text", "finalize")], "join")
        self.assertEqual(edges[("grok_image_set", "finalize")], "join")

        nodes = {node["node_key"]: node for node in result["workflow_diagram_nodes"]}
        self.assertEqual(nodes["openai_text"]["column"], 0)
        self.assertEqual(nodes["grok_image_set"]["column"], 2)
        self.assertTrue(nodes["openai_text_skill.generate_xhs_text"]["editable"])
        self.assertTrue(nodes["grok_image_skill.compose_page_prompts"]["editable"])

        panels = {panel["panel_key"]: panel for panel in result["operator_edit_panels"]}
        self.assertIn("openai_text_skill", panels)
        self.assertIn("grok_image_skill", panels)
        control_keys = {
            control["control_key"]
            for panel in result["operator_edit_panels"]
            for control in panel["controls"]
        }
        self.assertIn("openai_text_skill_prompt", control_keys)
        self.assertIn("grok_image_skill_prompt", control_keys)
        self.assertIn("image_aspect_ratio", control_keys)

    def test_plain_operator_fields_modify_skills_without_json(self):
        input_data = base_input()
        input_data.pop("skill_flow_overrides")
        input_data.update(
            {
                "image_aspect_ratio": "4:5",
                "openai_text_skill_prompt": "普通表单改OpenAI：更像运营复盘，不要技术黑话。",
                "grok_visual_rules_prompt": "普通表单改视觉规则：粉蓝色板、圆角角色、留出标题区。",
                "grok_image_skill_prompt": "普通表单改Grok：4:5卡通套图，每页只画一个动作。",
                "openai_review_enabled": False,
                "grok_review_enabled": False,
            }
        )

        result = main_graph.invoke(input_data)
        openai_steps = {step["step_key"]: step for step in result["skill_subflows"][0]["steps"]}
        grok_steps = {step["step_key"]: step for step in result["skill_subflows"][1]["steps"]}
        self.assertIn("普通表单改OpenAI", openai_steps["generate_xhs_text"]["final_prompt"])
        self.assertFalse(openai_steps["review_text_for_image"]["enabled"])
        self.assertIn("普通表单改视觉规则", grok_steps["load_visual_rules"]["final_prompt"])
        self.assertIn("普通表单改Grok", grok_steps["compose_page_prompts"]["final_prompt"])
        self.assertFalse(grok_steps["review_set_consistency"]["enabled"])

        text_request = result["openai_text_package"]["request"]
        image_request = result["grok_image_set"]["images"][0]["request"]
        self.assertIn("普通表单改OpenAI", text_request["payload"]["input"])
        self.assertIn("普通表单改Grok", image_request["payload"]["prompt"])
        self.assertEqual(image_request["payload"]["aspect_ratio"], "4:5")

    def test_dry_run_requests_call_the_corresponding_skill_subflows(self):
        result = main_graph.invoke(base_input())

        text_request = result["openai_text_package"]["request"]
        self.assertEqual(text_request["skill_key"], "openai_text_skill")
        self.assertEqual(text_request["prompt_key"], "openai_text_skill")
        self.assertTrue(text_request["dry_run"])
        self.assertEqual(text_request["payload"]["reasoning"]["effort"], "xhigh")
        self.assertIn("运营改写OpenAI子流程", text_request["payload"]["input"])
        self.assertNotIn("review_text_for_image", text_request["payload"]["input"])
        self.assertNotIn("把文字转成图片 brief 并审核", text_request["payload"]["input"])

        image_request = result["grok_image_set"]["images"][0]["request"]
        self.assertEqual(image_request["skill_key"], "grok_image_skill")
        self.assertEqual(image_request["prompt_key"], "grok_image_skill")
        self.assertTrue(image_request["dry_run"])
        self.assertIn("运营改写Grok子流程", image_request["payload"]["prompt"])

        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("sk-test_secret", serialized)
        self.assertNotIn("gsk_test_secret", serialized)

    def test_mock_live_calls_use_subflow_payloads_and_return_image_urls(self):
        original_openai_post_json = openai_module.post_json
        original_grok_post_json = grok_module.post_json
        calls = {"openai": 0, "grok": 0}

        def fake_openai(endpoint, api_key, payload, timeout=90):
            calls["openai"] += 1
            self.assertEqual(endpoint, "https://api.openai.com/v1/responses")
            self.assertEqual(api_key, "sk-test_secret_123456789")
            self.assertEqual(payload["reasoning"]["effort"], "xhigh")
            self.assertIn("运营改写OpenAI子流程", payload["input"])
            self.assertNotIn("Authorization", json.dumps(payload, ensure_ascii=False))
            return {
                "output_text": json.dumps(
                    {
                        "title_options": ["A", "B", "C"],
                        "card_script": [
                            "封面：AI副业先别乱学工具",
                            "痛点：没有基础也能先验证需求",
                            "证据：看评论里的真实卡点",
                            "方法：用三步筛选最小选题",
                            "行动：今天整理五条评论",
                            "收口：把结果写回选题库",
                        ],
                        "post_description": "先验证需求，再生成卡片。",
                        "image_brief": "统一主角、明亮色板、3:4卡通套图。",
                    },
                    ensure_ascii=False,
                )
            }

        def fake_grok(endpoint, api_key, payload, timeout=120):
            calls["grok"] += 1
            self.assertEqual(endpoint, "https://api.x.ai/v1/images/generations")
            self.assertEqual(api_key, "gsk_test_secret_123456789")
            self.assertEqual(payload["model"], "grok-imagine-image-quality")
            self.assertEqual(payload["aspect_ratio"], "3:4")
            self.assertEqual(payload["response_format"], "url")
            self.assertIn("运营改写Grok子流程", payload["prompt"])
            self.assertNotIn("AI副业先别乱学工具", payload["prompt"])
            self.assertNotIn("Authorization", json.dumps(payload, ensure_ascii=False))
            return {"data": [{"url": f"https://example.com/xhs-{calls['grok']}.png"}]}

        try:
            openai_module.post_json = fake_openai
            grok_module.post_json = fake_grok
            result = main_graph.invoke(base_input(execute_model_calls=True))
        finally:
            openai_module.post_json = original_openai_post_json
            grok_module.post_json = original_grok_post_json

        self.assertEqual(calls, {"openai": 1, "grok": 6})
        self.assertEqual(result["openai_text_package"]["status"], "completed")
        self.assertFalse(result["openai_text_package"]["request"]["dry_run"])
        self.assertEqual(result["grok_image_set"]["status"], "completed")
        self.assertEqual(result["grok_image_set"]["images"][0]["image_url"], "https://example.com/xhs-1.png")

        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("sk-test_secret", serialized)
        self.assertNotIn("gsk_test_secret", serialized)


if __name__ == "__main__":
    unittest.main()
