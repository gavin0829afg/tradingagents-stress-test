"""Offline tests for the Week 1 pilot runner."""

import json
from pathlib import Path

import yaml
from langchain_core.messages import AIMessage

from src import pilot


def _config(path: Path, runs: list[dict] | None = None) -> Path:
    payload = {
        "experiment": "pilot",
        "settings": {
            "llm_provider": "ollama",
            "backend_url": "http://localhost:11434/v1",
            "temperature": 0.7,
            "num_ctx": 8192,
            "selected_analysts": ["market", "fundamentals"],
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1,
            "variant": "normal",
            "config": "full",
        },
        "runs": runs or [{
            "case_id": "jpm-2023-03-10",
            "ticker": "JPM",
            "decision_date": "2023-03-10",
            "period": "IS",
            "seed": 1,
        }],
    }
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def test_generate_run_id_is_safe_and_unique():
    first = pilot.generate_run_id("jpm/2023-03-10", 1)
    second = pilot.generate_run_id("jpm/2023-03-10", 1)
    assert first != second
    assert "/" not in first and "\\" not in first
    assert first.startswith("jpm-2023-03-10-s1-")


def test_build_run_config_maps_seed_and_isolates_paths(tmp_path):
    run_dir = tmp_path / "pilot" / "jpm-run"
    config_path = _config(tmp_path / "config.yaml")
    settings = yaml.safe_load(config_path.read_text(encoding="utf-8"))["settings"]
    config = pilot.build_run_config(
        settings,
        2,
        run_dir,
        tmp_path / "cache",
        base_config={"unrelated": "preserved"},
    )
    assert config["llm_provider"] == "ollama"
    assert config["backend_url"] == "http://localhost:11434/v1"
    assert config["quick_think_llm"] == config["deep_think_llm"] == "llama3.1-8k-s2"
    assert config["temperature"] == 0.7
    assert config["max_debate_rounds"] == config["max_risk_discuss_rounds"] == 1
    assert config["memory_log_path"] == str(run_dir / "trading_memory.md")
    assert config["results_dir"] == str(run_dir)
    assert config["data_cache_dir"] == str(tmp_path / "cache")
    assert config["unrelated"] == "preserved"


def test_all_six_cases_are_configured_with_one_repeat():
    config = pilot.load_pilot_config(Path("configs/pilot.yaml"))
    assert len(config["runs"]) == 6
    assert [row["ticker"] for row in config["runs"]] == ["JPM", "JPM", "RY", "BAC", "WFC", "JPM"]
    assert all(row["seed"] == 1 for row in config["runs"])
    assert config["runs"][-1]["replicate_of"] == config["runs"][0]["case_id"]


def test_position_mapping_and_unknown_rating():
    expected = {
        "Buy": 1.0,
        "Overweight": 0.5,
        "Hold": 0.0,
        "Underweight": -0.5,
        "Sell": -1.0,
    }
    assert {rating: pilot.position_for_rating(rating) for rating in expected} == expected
    assert pilot.position_for_rating("REVIEW") is None
    assert pilot.position_for_rating("unknown") is None


def test_timeout_exceptions_keep_timeout_status():
    class APITimeoutError(Exception):
        pass

    assert pilot._status_for_exception(TimeoutError("slow")) == "timeout"
    assert pilot._status_for_exception(APITimeoutError("slow")) == "timeout"
    assert pilot._status_for_exception(RuntimeError("failure")) == "tool_error"


def test_review_is_parse_error_exception_is_tool_error_and_logs_append(tmp_path):
    config_file = _config(tmp_path / "pilot.yaml", runs=[
        {"case_id": "review", "ticker": "JPM", "decision_date": "2023-03-10", "period": "IS", "seed": 1},
        {"case_id": "unknown", "ticker": "WFC", "decision_date": "2025-05-02", "period": "OOS", "seed": 1},
        {"case_id": "failed", "ticker": "BAC", "decision_date": "2023-05-05", "period": "IS", "seed": 1},
    ])
    graph_paths = []

    class FakeGraph:
        def __init__(self, *, selected_analysts, config, callbacks):
            assert selected_analysts == ["market", "fundamentals"]
            memory_path = Path(config["memory_log_path"])
            result_dir = Path(config["results_dir"])
            assert memory_path.parent == result_dir
            assert memory_path.exists() and memory_path.read_text(encoding="utf-8") == ""
            assert config["data_cache_dir"] == str((tmp_path / "results" / "raw" / "cache").resolve())
            graph_paths.append(memory_path)
            self.callbacks = callbacks

        def propagate(self, ticker, decision_date):
            if ticker == "BAC":
                raise RuntimeError("synthetic failure")
            rating = "unknown" if ticker == "WFC" else "REVIEW"
            return {"ticker": ticker, "date": decision_date}, rating

    raw_root = tmp_path / "results" / "raw"
    rows = pilot.run_pilot(config_file, "gav", machine="test-gpu", raw_root=raw_root,
                           graph_factory=FakeGraph, ta_commit="test-commit")
    assert [row["status"] for row in rows] == ["parse_error", "parse_error", "tool_error"]
    assert rows[2]["error"] == "RuntimeError: synthetic failure"
    assert len(set(graph_paths)) == 3
    assert all(path.is_relative_to(raw_root / "pilot") for path in graph_paths)
    log_path = raw_root / "pilot.jsonl"
    first_lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(first_lines) == 3

    rerun_rows = pilot.run_pilot(config_file, "gav", machine="test-gpu", raw_root=raw_root,
                                 graph_factory=FakeGraph, ta_commit="test-commit")
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 6
    assert {row["run_id"] for row in rows}.isdisjoint(row["run_id"] for row in rerun_rows)


def test_ok_run_saves_final_state_and_token_metadata(tmp_path):
    config_file = _config(tmp_path / "pilot.yaml")

    class FakeGraph:
        def __init__(self, *, selected_analysts, config, callbacks):
            self.callbacks = callbacks

        def propagate(self, ticker, decision_date):
            return {"ticker": ticker, "date": decision_date, "result": "saved"}, "Buy"

    raw_root = tmp_path / "raw"
    rows = pilot.run_pilot(config_file, "aya", machine="test-gpu", raw_root=raw_root,
                           graph_factory=FakeGraph, ta_commit="test-commit")
    row = rows[0]
    assert row["status"] == "ok" and row["position"] == 1.0
    # The fixture raw root is outside the repository, so the absolute path is omitted in the row.
    final_state = next((raw_root / "pilot").glob("*/final_state.json"))
    assert json.loads(final_state.read_text(encoding="utf-8"))["result"] == "saved"
    assert row["max_prompt_tokens"] is None
    assert row["machine"] == "test-gpu"


def test_token_usage_recorder_reads_common_usage_metadata():
    class Response:
        llm_output = {"token_usage": {"prompt_tokens": 120, "total_tokens": 180}}
        generations = []

    recorder = pilot.TokenUsageRecorder()
    recorder.on_llm_end(Response())
    assert recorder.max_prompt_tokens == 120
    assert recorder.total_tokens == 180


def test_final_state_serializer_preserves_langchain_message_content():
    encoded = json.dumps({"messages": [AIMessage(content="BUY")], "run": 1},
                         default=pilot._json_default)
    decoded = json.loads(encoded)
    assert decoded["messages"][0]["content"] == "BUY"
    assert decoded["run"] == 1
