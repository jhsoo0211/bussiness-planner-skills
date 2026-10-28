#!/usr/bin/env python3
"""디자인 추천의 내용 보존·브랜드 우선·테마 호환 회귀 검사(표준 라이브러리)."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/bizplan-slides/scripts"))
import design_advisor as advisor


class DesignAdvisorTests(unittest.TestCase):
    def setUp(self):
        self.units = [
            {"id": "U01", "code": "R19", "pattern": "rows", "where": "문제와 해결",
             "spec": {"type": "rows", "title": "문제와 해결", "items": [
                 {"label": "폐기", "title": "원료 회수"}, {"label": "판로", "title": "로컬 납품"}]}},
            {"id": "U02", "code": "R5", "pattern": "kpi", "spec": {"type": "kpi", "title": "예시 지표",
             "items": [{"value": "12곳", "label": "가정"}, {"value": "30%", "label": "목표"}]}},
        ]

    def test_context_changes_only_design(self):
        before = deepcopy(self.units)
        for context, expected in [({"industry": "친환경"}, "forest-mint"),
                                  ({"industry": "식품·로컬"}, "warm-sand"),
                                  ({"industry": "교육"}, "plum-soft"),
                                  ({"tone": "대담한 라임"}, "lime-ink"),
                                  ({"industry": "인공지능"}, "report-blue")]:
            result, theme = advisor.recommend(self.units, context)
            self.assertEqual(result["theme"], expected)
            self.assertEqual(theme["name"], expected)
            self.assertEqual([(u["id"], u["code"], u["pattern"]) for u in result["units"]],
                             [(u["id"], u["code"], u["pattern"]) for u in before])
            self.assertEqual(self.units, before)

    def test_neutral_fallback_and_latin_boundaries(self):
        for context in ({}, {"item": "chair platform"}):
            result, _ = advisor.recommend(self.units, context)
            self.assertEqual(result["theme"], "mono-line")
            self.assertEqual(result["candidates"], [])

    def test_stated_tone_precedes_industry_hint(self):
        result, _ = advisor.recommend(self.units, {"industry": "교육", "tone": "차분한 모노"})
        self.assertEqual(result["theme"], "mono-line")

    def test_explicit_theme_and_brand_precede_hints(self):
        context = {"industry": "친환경", "theme": "warm-sand", "brand_primary": "FFFF00"}
        before = deepcopy(context)
        result, theme = advisor.recommend(self.units, context, "plum-soft", "#123456")
        self.assertEqual(result["theme"], "plum-soft")
        self.assertEqual(theme["colors"]["primary"], "123456")
        self.assertEqual(theme["colors"]["series"][0], "123456")
        self.assertEqual(context, before)

    def test_light_brand_preserves_original_and_readable_accent(self):
        result, theme = advisor.recommend(self.units, {"brand_primary": "#FFFF00"})
        self.assertEqual(theme["brand_primary"], "FFFF00")
        self.assertGreaterEqual(advisor.white_contrast(theme["colors"]["primary"]), 4.5)
        self.assertIn("대비 조정", result["selection_reason"])

    def test_fixed_template_has_no_replacement_theme(self):
        result, theme = advisor.recommend(self.units, {"fixed_template": True, "theme": "missing"}, accent="#FFFF00")
        self.assertIsNone(theme)
        self.assertIsNone(result["palette"])
        self.assertEqual(result["mode"], "template-preserve")

    def test_pending_pattern_is_not_reclassified(self):
        units = [{"id": "U01", "code": "R5?", "pattern": "bullets"},
                 {"id": "U02", "code": "CUSTOM", "pattern": "custom-flow"}]
        result, _ = advisor.recommend(units, {})
        for source, target in zip(units, result["units"]):
            self.assertEqual(source["pattern"], target["pattern"])
            self.assertEqual(source["code"], target["code"])
            self.assertTrue(target["review_required"])
            self.assertEqual(target["reference_keys"], [])

    def test_reference_keys_match_observed_same_pattern(self):
        catalog = advisor.read_json(advisor.CATALOG)
        refs = {r["template_key"]: r for r in catalog["references"]}
        self.assertEqual(len(refs), 90)
        self.assertEqual(sum(r["status"] == "mapped" for r in refs.values()), 30)
        result, _ = advisor.recommend(self.units, {"industry": "친환경"})
        for unit in result["units"]:
            self.assertTrue(unit["reference_keys"])
            for key in unit["reference_keys"]:
                self.assertIn(unit["pattern"], refs[key]["patterns"])
                self.assertEqual(refs[key]["status"], "mapped")

    def test_known_pattern_without_reference_uses_existing_renderer(self):
        result, _ = advisor.recommend([{"id": "U01", "code": "R23", "pattern": "cover"}], {})
        self.assertEqual(result["units"][0]["reference_status"], "existing-pattern")

    def test_bad_context_and_color_fail_clearly(self):
        for context in ({"item": []}, {"fixed_template": "false"}, {"brand_primary": "not-a-color"}):
            with self.assertRaises(ValueError):
                advisor.recommend(self.units, context)

    def test_cli_preserves_parser_input_and_fixed_template(self):
        with tempfile.TemporaryDirectory(prefix="bizplan-design-") as tmp:
            d = Path(tmp)
            doc = d / "plan.md"
            doc.write_text("# 예시 사업\n\n## 문제와 해결\n| 문제 | 해결 |\n|---|---|\n| 폐기 | 원료 회수 |\n| 판로 | 로컬 납품 |\n", encoding="utf-8")
            source = d / "units.json"
            parsed = subprocess.run([sys.executable, "-B", str(ROOT / "skills/bizplan-slides/scripts/suggest_patterns.py"),
                                     str(doc), "--json", str(source)], capture_output=True, text=True)
            self.assertEqual(parsed.returncode, 0, parsed.stderr)
            units = advisor.read_json(source)
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            context = d / "context.json"
            context.write_text('{"fixed_template": true}', encoding="utf-8")
            cmd = [sys.executable, "-B", str(Path(advisor.__file__)), "--units", str(source),
                   "--context", str(context), "--out", str(d / "design.json"),
                   "--md", str(d / "design.md"), "--theme-out", str(d / "theme.json")]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            self.assertFalse((d / "theme.json").exists())
            self.assertEqual(advisor.read_json(d / "design.json")["units"][0]["pattern"], units[0]["pattern"])
            # 입력을 출력으로 지정해도 원본을 덮어쓰지 않는다.
            run = subprocess.run([*cmd[:cmd.index("--out")], "--out", str(source)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    def test_new_themes_work_with_existing_deck_and_visual_renderers(self):
        import theme_deck
        sys.path.insert(0, str(ROOT / "skills/bizplan-visual/scripts"))
        import html_visuals
        sample = advisor.read_json(advisor.THEMES / "sample-deck.json")
        self.assertEqual(theme_deck.validate(sample, str(advisor.THEMES))[0], [])
        visuals = {"visuals": [{"id": "test-kpi", "type": "kpi", "headline": "예시 지표",
                               "tiles": [{"value": "12곳", "label": "가정"}, {"value": "30%", "label": "목표"}]}]}
        for name in ("forest-mint", "warm-sand", "plum-soft", "lime-ink"):
            theme = theme_deck.load_theme(name)
            self.assertGreaterEqual(advisor.white_contrast(theme["colors"]["primary"]), 4.5)
            page = html_visuals.build(visuals, theme["colors"]["primary"], slide=True)
            self.assertIn("#" + theme["colors"]["primary"], page)
            self.assertIn("12곳", page)


if __name__ == "__main__":
    unittest.main(verbosity=2)
