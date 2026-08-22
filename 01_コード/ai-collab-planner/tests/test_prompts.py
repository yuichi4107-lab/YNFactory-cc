import unittest
from pathlib import Path

from ai_planner.config import load_settings
from ai_planner.prompts import (
    audit_forks,
    extract_forks_and_stances,
    final_check_requirements,
    finalize_plan,
    finalize_plan_without_debate,
    independent_plan,
    list_issues,
    mediate_round,
    respond_to_issues,
    solo_plan,
)


class PromptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = load_settings(Path(__file__).parents[1] / "config.toml")

    def _finalize(self) -> str:
        return finalize_plan(
            "目的本文",
            "立場Aの本文",
            "立場Bの本文",
            "争点表の本文",
            "調停の本文",
            "統合完了（1/2ラウンド）",
            self.settings.teams["standard"],
        )

    # --- 目的が「統合」であることの担保 -------------------------------

    def test_every_prompt_states_the_goal_is_integration_not_winning(self):
        prompts = (
            extract_forks_and_stances("目的"),
            audit_forks("目的", "分岐点の本文"),
            independent_plan("目的", "立場A", "立場の本文", "事実の本文"),
            list_issues("目的", "A本文", "B本文", "分岐点本文"),
            respond_to_issues("目的", "立場A", "立場", "自案", "文脈", 1),
            mediate_round("目的", "争点", "文脈", "A応答", "B応答", 1, 2),
            self._finalize(),
        )
        for prompt in prompts:
            self.assertIn("どちらが優れているかを決めるのではなく", prompt)
            self.assertIn("良いところを1つの設計へ組み込む", prompt)

    def test_no_prompt_asks_to_beat_the_other_plan(self):
        prompts = (
            independent_plan("目的", "立場A", "立場の本文", "事実の本文"),
            respond_to_issues("目的", "立場A", "立場", "自案", "文脈", 1),
            mediate_round("目的", "争点", "文脈", "A応答", "B応答", 1, 2),
        )
        for prompt in prompts:
            self.assertNotIn("優れた案を書け", prompt)
            self.assertNotIn("採用すべき要素", prompt)
            self.assertNotIn("除外すべき要素", prompt)

    # --- 分岐点と立場 -------------------------------------------------

    def test_fork_extraction_orders_by_irreversibility_and_requires_discards(self):
        prompt = extract_forks_and_stances("目的")
        self.assertIn("後から覆すときのコストが大きい順", prompt)
        self.assertIn("### 捨てるもの", prompt)
        self.assertIn("片方をわざと劣った案にしない", prompt)
        self.assertIn("`なし`", prompt)

    def test_fork_audit_only_adds_missing_forks(self):
        prompt = audit_forks("目的", "分岐点の本文")
        self.assertIn("分岐点の本文", prompt)
        self.assertIn("抜けている分岐点を見つけて追加すること", prompt)
        self.assertIn("補完後の全文", prompt)

    def test_independent_plan_carries_stance_and_facts(self):
        prompt = independent_plan("目的本文", "立場A", "立場の本文", "事実の本文")
        for value in ("目的本文", "立場の本文", "事実の本文"):
            self.assertIn(value, prompt)
        self.assertIn("要件定義案と実装プラン案", prompt)
        self.assertIn("コード実装", prompt)
        self.assertIn("変更しない", prompt)

    # --- 争点と応答 ---------------------------------------------------

    def test_issue_list_forbids_ranking_the_plans(self):
        prompt = list_issues("目的", "A本文", "B本文", "分岐点本文")
        for value in ("A本文", "B本文", "分岐点本文"):
            self.assertIn(value, prompt)
        self.assertIn("どちらが優れているかは書かないでください", prompt)
        self.assertIn("# 争点表", prompt)

    def test_response_offers_integration_choices_not_win_lose(self):
        prompt = respond_to_issues("目的", "立場A", "立場本文", "自案本文", "文脈本文", 2)
        for value in ("立場本文", "自案本文", "文脈本文"):
            self.assertIn(value, prompt)
        for choice in ("**取り込む**", "**両立させる**", "**両立しない**"):
            self.assertIn(choice, prompt)
        self.assertIn("相手を論破することではありません", prompt)
        self.assertIn("なぜ工夫では解決できないのか", prompt)
        self.assertIn("前のラウンドで出していない新しい根拠", prompt)

    def test_mediation_requires_both_sides_contributions_and_fixed_tokens(self):
        prompt = mediate_round("目的", "争点本文", "文脈本文", "A応答本文", "B応答本文", 2, 3)
        for value in ("争点本文", "文脈本文", "A応答本文", "B応答本文"):
            self.assertIn(value, prompt)
        self.assertIn("片方しか書けないなら、それは統合ではなく選別です", prompt)
        self.assertIn("この状態が残るのは失敗ではありません", prompt)
        self.assertIn("未整理: N件", prompt)
        for token in ("`続行`", "`終了：統合完了`", "`終了：停滞`"):
            self.assertIn(token, prompt)

    # --- 統合と最終チェック -------------------------------------------

    def test_finalization_contains_all_source_contents(self):
        prompt = self._finalize()
        for value in ("目的本文", "立場Aの本文", "立場Bの本文", "争点表の本文", "調停の本文"):
            self.assertIn(value, prompt)

    def test_finalization_forbids_adopting_one_plan_wholesale(self):
        prompt = self._finalize()
        self.assertIn("どちらか一方の案をそのまま採用してはいけません", prompt)
        self.assertIn("## 14. 争点と統合結果", prompt)
        self.assertIn("立場Aから採った要素", prompt)
        self.assertIn("立場Bから採った要素", prompt)

    def test_finalization_requires_model_family_selection(self):
        prompt = self._finalize()
        self.assertIn("Claude系とGPT系から工程別に選び直してください", prompt)
        self.assertIn("### 13.3 AIモデルの役割分担", prompt)
        self.assertIn("代替候補", prompt)

    def test_no_debate_paths_still_require_all_headings(self):
        for prompt in (
            finalize_plan_without_debate("目的", "案の本文", self.settings.teams["light"]),
            solo_plan("目的", "事実の本文"),
        ):
            self.assertIn("目的", prompt)
        prompt = finalize_plan_without_debate("目的", "案の本文", self.settings.teams["light"])
        self.assertIn("## 14. 争点と統合結果", prompt)
        self.assertIn("議論を行っていないため該当なし", prompt)

    def test_final_check_detects_selection_disguised_as_integration(self):
        prompt = final_check_requirements("目的", "# 要件定義書・実装プラン\n本文", "争点表本文")
        self.assertIn("争点表本文", prompt)
        self.assertIn("修正を反映した完成版全文", prompt)
        self.assertIn("実装は行わない", prompt)
        self.assertIn("Claude系／GPT系", prompt)
        self.assertIn("片方の案の要素しか入っていない争点がないか", prompt)


if __name__ == "__main__":
    unittest.main()
