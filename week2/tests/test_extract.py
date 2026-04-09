import os
import pytest

pytest.importorskip("ollama")

from ..app.services.extract import (
    ActionItemList,
    extract_action_items,
    extract_action_items_llm,
)


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


def _require_ollama():
    if os.getenv("RUN_OLLAMA_TESTS") != "1":
        pytest.skip("Set RUN_OLLAMA_TESTS=1 to run LLM-backed tests.")


def _print_result(title: str, result: ActionItemList) -> None:
    print(f"\n{title}:")
    print(result.model_dump_json(indent=2, exclude_none=False))


def test_extract_action_items_llm_standard_bullet_lists():
    _require_ollama()
    text = """
    - Set up project repository
    - Assign frontend tasks to Alice
    - Prioritize database migration as high
    """.strip()

    result = extract_action_items_llm(text)
    _print_result("standard_bullet_lists", result)

    assert isinstance(result, ActionItemList)
    assert isinstance(result.action_items, list)
    assert len(result.action_items) >= 1
    assert any(item.task.strip() for item in result.action_items)


def test_extract_action_items_llm_keyword_prefixed_lines():
    _require_ollama()
    text = """
    TODO: finalize the API spec with Bob (high priority)
    Action: prepare release notes and assign to Carol
    Next: schedule QA regression run
    """.strip()

    result = extract_action_items_llm(text)
    _print_result("keyword_prefixed_lines", result)

    assert isinstance(result, ActionItemList)
    assert len(result.action_items) >= 1
    assert any(item.task.strip() for item in result.action_items)


@pytest.mark.parametrize("text", ["", "   \n\t  "])
def test_extract_action_items_llm_empty_and_whitespace(text: str):
    _require_ollama()
    result = extract_action_items_llm(text)
    _print_result("empty_or_whitespace", result)

    assert isinstance(result, ActionItemList)
    assert result.action_items == []


def test_extract_action_items_llm_natural_language_implicit_task():
    _require_ollama()
    text = (
        "The production report still has inconsistent totals, and we should "
        "verify the ETL pipeline before Friday so finance can close the month."
    )

    result = extract_action_items_llm(text)
    _print_result("natural_language_implicit_task", result)

    assert isinstance(result, ActionItemList)
    assert len(result.action_items) >= 1
    assert any(item.task.strip() for item in result.action_items)
