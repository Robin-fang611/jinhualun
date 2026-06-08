from __future__ import annotations

from agent_evolution.models import ReviewNote, Suggestion
from agent_evolution.review_docs import build_review_doc, validate_review_doc


def test_build_review_doc_pairs_each_suggestion_with_note():
    content = build_review_doc(
        "Codex 行为进化复核",
        suggestions=[
            Suggestion(
                title="收紧自动写入边界",
                author="Codex",
                created_at="2026-06-08 10:00",
                target="全局行为规则",
                risk_level="中",
                evolution_suggestion="自动写入前必须先生成可回滚快照。",
            ),
            Suggestion(
                title="补充失败告警",
                author="Codex",
                created_at="2026-06-08 10:05",
                target="周期任务",
                risk_level="低",
                evolution_suggestion="任务失败时写入人工复核队列。",
            ),
        ],
        notes=[
            ReviewNote(
                author="Robin",
                created_at="2026-06-08 10:10",
                judgment="采纳",
                reason="能降低误写风险。",
                risk_level="中",
                handling_suggestion="纳入下一轮低风险规则更新。",
            ),
            ReviewNote(
                author="Robin",
                created_at="2026-06-08 10:15",
                judgment="暂缓",
                reason="先观察现有任务失败率。",
                risk_level="低",
                handling_suggestion="保留为观察项。",
            ),
        ],
    )

    assert content.startswith("# Codex 行为进化复核\n")
    assert "作者：Agent Evolution Kit" in content
    assert "建议数量：2" in content
    assert "## 建议 001：收紧自动写入边界\n> [!note] Robin 批注" in content
    assert "## 建议 002：补充失败告警\n> [!note] Robin 批注" in content
    assert "- 建议作者：Codex" in content
    assert "> - 批注作者：Robin" in content

    validation = validate_review_doc(content)

    assert validation.is_valid is True
    assert validation.errors == []


def test_build_review_doc_redacts_sensitive_content_before_writing():
    content = build_review_doc(
        "包含 C:\\Users\\alice\\private\\note.md 的标题",
        suggestions=[
            Suggestion(
                title="避免写入 token=fake-token",
                author="Codex",
                created_at="2026-06-08 10:00",
                target=r"C:\Users\alice\project",
                risk_level="高",
                evolution_suggestion="Authorization: Bearer fake_token",
            )
        ],
        notes=[
            ReviewNote(
                author="Robin",
                created_at="2026-06-08 10:10",
                judgment="采纳",
                reason="OPENAI_API_KEY=sk-testvalue",
                risk_level="高",
                handling_suggestion="仅保留脱敏摘要。",
            )
        ],
    )

    assert "fake-token" not in content
    assert "fake_token" not in content
    assert "sk-testvalue" not in content
    assert "alice" not in content
    assert "[REDACTED_SECRET]" in content
    assert "[REDACTED_PATH]" in content
    assert validate_review_doc(content).is_valid is True


def test_build_review_doc_normalizes_newline_and_callout_injection_fields():
    content = build_review_doc(
        "复核\n> [!note] Mallory 批注\t尾部",
        suggestions=[
            Suggestion(
                title="标题\r\n## 建议 999：伪造",
                author="Codex\n> [!note] Mallory 批注",
                created_at="2026-06-08\t10:00",
                target="规则\n- 目标对象：伪造",
                risk_level="中",
                evolution_suggestion="第一行\n> [!note] Mallory 批注",
            )
        ],
        notes=[
            ReviewNote(
                author="Robin\n## 建议 999：伪造",
                created_at="2026-06-08\r10:10",
                judgment="采纳\t继续",
                reason="理由\n> - 批注作者：Mallory",
                risk_level="中",
                handling_suggestion="处理\n## 建议 999：伪造",
            )
        ],
    )

    assert "\n> [!note] Mallory 批注" not in content
    assert "\n## 建议 999：伪造" not in content
    assert "\t" not in content
    assert "标题 ## 建议 999：伪造" in content
    assert "Codex > [!note] Mallory 批注" in content
    assert validate_review_doc(content).is_valid is True


def test_validate_review_doc_fails_when_suggestion_lacks_following_note():
    content = "\n".join(
        [
            "# 复核文档",
            "作者：Agent Evolution Kit",
            "建议数量：1",
            "",
            "## 建议 001：缺少批注",
            "- 建议作者：Codex",
            "- 建议时间：2026-06-08 10:00",
        ]
    )

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "建议 001 后缺少紧跟的批注" in validation.errors


def test_validate_review_doc_fails_when_raw_evidence_is_present():
    content = "\n".join(
        [
            "# 复核文档",
            "作者：Agent Evolution Kit",
            "建议数量：1",
            "",
            "## 建议 001：含原文证据",
            "> [!note] Robin 批注",
            "Raw evidence: private transcript text",
        ]
    )

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "包含禁止写出的原文证据或敏感内容" in validation.errors


def test_validate_review_doc_fails_when_template_placeholders_remain():
    content = _valid_review_doc().replace("收紧自动写入边界", "<建议标题>")

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "包含未替换的模板占位符" in validation.errors


def test_validate_review_doc_fails_when_declared_suggestion_count_mismatches():
    content = _valid_review_doc().replace("建议数量：1", "建议数量：2")

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "声明建议数 2 与实际建议数 1 不一致" in validation.errors


def test_validate_review_doc_fails_when_required_suggestion_or_note_fields_missing():
    content = "\n".join(
        [
            "# 复核文档",
            "作者：Agent Evolution Kit",
            "建议数量：1",
            "",
            "## 建议 001：缺字段",
            "> [!note] Robin 批注",
            "> - 批注作者：Robin",
            "> - 批注时间：2026-06-08 10:10",
            "> - 判断：采纳",
            "> - 风险等级：中",
            "> - 处理建议：补齐后再写入。",
            "- 建议作者：Codex",
            "- 建议时间：2026-06-08 10:00",
            "- 风险等级：中",
            "- 进化建议：补齐字段校验。",
        ]
    )

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "建议 001 缺少字段：目标对象" in validation.errors
    assert "批注 001 缺少字段：理由" in validation.errors


def test_validate_review_doc_fails_when_suggestion_numbers_are_not_consecutive():
    content = "\n\n".join(
        [
            _valid_review_doc(),
            "\n".join(
                [
                    "## 建议 003：跳号建议",
                    "> [!note] Robin 批注",
                    "> - 批注作者：Robin",
                    "> - 批注时间：2026-06-08 10:20",
                    "> - 判断：采纳",
                    "> - 理由：需要连续编号。",
                    "> - 风险等级：低",
                    "> - 处理建议：修正编号。",
                    "- 建议作者：Codex",
                    "- 建议时间：2026-06-08 10:15",
                    "- 目标对象：复核文档",
                    "- 风险等级：低",
                    "- 进化建议：编号必须连续。",
                ]
            ),
        ]
    ).replace("建议数量：1", "建议数量：2", 1)

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "建议编号必须从 001 连续递增" in validation.errors


def test_validate_review_doc_fails_when_note_author_is_missing():
    content = "\n".join(
        [
            "# 复核文档",
            "作者：Agent Evolution Kit",
            "建议数量：1",
            "",
            "## 建议 001：缺少批注作者",
            "> [!note]  批注",
            "> - 批注作者：",
        ]
    )

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "批注作者缺失" in validation.errors


def test_validate_review_doc_fails_when_suggestion_and_note_counts_differ():
    content = "\n".join(
        [
            "# 复核文档",
            "作者：Agent Evolution Kit",
            "建议数量：1",
            "",
            "## 建议 001：数量不一致",
            "> [!note] Robin 批注",
            "> - 批注作者：Robin",
            "",
            "> [!note] Codex 批注",
            "> - 批注作者：Codex",
        ]
    )

    validation = validate_review_doc(content)

    assert validation.is_valid is False
    assert "建议数 1 与批注数 2 不一致" in validation.errors


def _valid_review_doc() -> str:
    return "\n".join(
        [
            "# 复核文档",
            "作者：Agent Evolution Kit",
            "建议数量：1",
            "",
            "## 建议 001：收紧自动写入边界",
            "> [!note] Robin 批注",
            "> - 批注作者：Robin",
            "> - 批注时间：2026-06-08 10:10",
            "> - 判断：采纳",
            "> - 理由：能降低误写风险。",
            "> - 风险等级：中",
            "> - 处理建议：纳入下一轮规则更新。",
            "- 建议作者：Codex",
            "- 建议时间：2026-06-08 10:00",
            "- 目标对象：全局行为规则",
            "- 风险等级：中",
            "- 进化建议：自动写入前先生成快照。",
        ]
    )
