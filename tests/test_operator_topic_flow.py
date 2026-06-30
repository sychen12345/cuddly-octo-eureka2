import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from graphs.state import DemandInsight, GraphInput, ProcessNodeInput
from graphs.nodes import process_node as process_module
from graphs.nodes.finalize_node import _build_card_package, _build_workflow_diagram


class _Runtime:
    context = None


class OperatorTopicFlowTests(unittest.TestCase):
    def test_runtime_requires_openai_and_grok_keys(self):
        with self.assertRaises(ValidationError):
            GraphInput(user_request="帮我做一组小红书卡片")

        payload = GraphInput(
            user_request="帮我做一组小红书卡片",
            openai_api_key="sk-test",
            grok_api_key="gsk-test",
        )
        self.assertEqual(payload.openai_api_key, "sk-test")
        self.assertEqual(payload.grok_api_key, "gsk-test")

    def test_operator_selected_hashtag_wins_without_hardcoded_topic(self):
        state = ProcessNodeInput(
            niche="运营填写的赛道",
            audience="目标用户",
            user_selected_topic="#运营指定话题",
            demand_insights=[
                DemandInsight(
                    cluster="核心需求",
                    user_words=["用户原话"],
                    pain="痛点",
                    desired_outcome="想要结果",
                    content_angle="内容角度",
                )
            ],
        )

        result = process_module.process_node(state, {}, _Runtime())

        self.assertEqual(result.selected_topic.title, "#运营指定话题")
        self.assertIn("#运营指定话题", result.selected_topic.hashtags)
        package = _build_card_package(result.selected_topic, {}, {}, 1)
        self.assertEqual(package["hashtags"], ["#运营指定话题"])

    def test_competitor_link_uses_openai_web_search_for_topics(self):
        calls = []

        def fake_web_search(api_key, system_prompt="", user_prompt="", **kwargs):
            calls.append((api_key, system_prompt, user_prompt, kwargs))
            return json.dumps(
                {
                    "topic_bank": [
                        {
                            "title": "从竞品评论里提炼出的新选题",
                            "audience": "目标用户",
                            "hook": "先看竞品评论里反复出现的问题。",
                            "demand_source": "OpenAI 联网查询竞品链接后提取",
                            "hashtags": ["#竞品洞察"],
                            "outline": ["拆竞品结构", "提炼评论需求", "给出差异化角度"],
                            "proof_needed": ["竞品链接公开信息"],
                            "differentiation": "只学习结构，不复制原文。",
                            "priority": "high",
                            "expected_view_score": 88,
                            "view_evidence": ["来自公开竞品链接和搜索结果"],
                        }
                    ]
                },
                ensure_ascii=False,
            )

        original = process_module.call_openai_web_search
        try:
            process_module.call_openai_web_search = fake_web_search
            state = ProcessNodeInput(
                niche="运营填写的赛道",
                audience="目标用户",
                xiaohongshu_url="https://www.xiaohongshu.com/explore/example",
                openai_api_key="sk-test",
                execute_model_calls=True,
            )
            result = process_module.process_node(state, {}, _Runtime())
        finally:
            process_module.call_openai_web_search = original

        self.assertEqual(calls[0][0], "sk-test")
        self.assertIn("必须使用联网搜索工具", calls[0][1])
        self.assertIn("https://www.xiaohongshu.com/explore/example", calls[0][2])
        self.assertEqual(result.selected_topic.title, "从竞品评论里提炼出的新选题")
        self.assertEqual(result.selected_topic.hashtags, ["#竞品洞察"])

    def test_finalize_node_does_not_guess_or_fallback_hashtags(self):
        package = _build_card_package(
            {"title": "没有显式话题标签的选题", "hashtags": []},
            {},
            {},
            1,
        )
        self.assertEqual(package["hashtags"], [])

        source = Path("src/graphs/nodes/finalize_node.py").read_text(encoding="utf-8")
        self.assertNotIn("_STOP_WORDS", source)
        self.assertNotIn("#小红书运营", source)
        self.assertNotIn("#内容选题", source)
        self.assertNotIn("#选题库", source)

    def test_workflow_diagram_uses_operator_business_language(self):
        diagram = _build_workflow_diagram()
        visible_text = json.dumps(diagram, ensure_ascii=False)

        for forbidden in ["配置", "同步", "回写", "规则变更", "步骤变更", "路由"]:
            self.assertNotIn(forbidden, visible_text)

        required_titles = {
            "运营需求入口",
            "竞品和用户需求分析",
            "爆款选题机会池",
            "图片制作技能",
            "文案技能：拆步骤",
            "图片技能：拆步骤",
            "AI生成小红书文案",
            "AI生成小红书套图",
            "成品审核与复盘建议",
        }
        actual_titles = {node["title"] for node in diagram["nodes"]}
        self.assertTrue(required_titles.issubset(actual_titles))


if __name__ == "__main__":
    unittest.main()
