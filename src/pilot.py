"""Run the six configured Week 1 pilot calls and append their outcomes."""

from __future__ import annotations

import argparse
import json
import logging
import platform
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import yaml
from langchain_core.callbacks import BaseCallbackHandler

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

logger = logging.getLogger(__name__)

RATING_POSITIONS = {
    "Buy": 1.0,
    "Overweight": 0.5,
    "Hold": 0.0,
    "Underweight": -0.5,
    "Sell": -1.0,
}

_SECRET_PATTERNS = (
    re.compile(r"(?i)((?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|password|secret)\s*[:=]\s*)\S+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)\S+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
)


class TokenUsageRecorder(BaseCallbackHandler):
    """Collect prompt and total token counts exposed by LangChain responses."""

    def __init__(self) -> None:
        self.prompt_token_counts: list[int] = []
        self._total_tokens: list[int] = []

    @staticmethod
    def _usage_maps(response: Any) -> list[dict[str, Any]]:
        maps: list[dict[str, Any]] = []
        llm_output = getattr(response, "llm_output", None) or {}
        if isinstance(llm_output, dict):
            maps.extend(
                value for key in ("token_usage", "usage")
                if isinstance((value := llm_output.get(key)), dict)
            )
        for generation_list in getattr(response, "generations", None) or []:
            for generation in generation_list:
                message = getattr(generation, "message", None)
                if message is None:
                    continue
                for attr in ("usage_metadata", "response_metadata"):
                    value = getattr(message, attr, None)
                    if isinstance(value, dict):
                        maps.append(value)
                        nested = value.get("token_usage") or value.get("usage")
                        if isinstance(nested, dict):
                            maps.append(nested)
        return maps

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Record counts when the provider exposes usage metadata."""
        usage_maps = self._usage_maps(response)
        prompt = next((
            usage.get(key) for usage in usage_maps
            for key in ("prompt_tokens", "input_tokens", "prompt_eval_count")
            if isinstance(usage.get(key), int) and not isinstance(usage.get(key), bool)
        ), None)
        total = next((
            usage.get(key) for usage in usage_maps
            for key in ("total_tokens", "total_token_count")
            if isinstance(usage.get(key), int) and not isinstance(usage.get(key), bool)
        ), None)
        if prompt is not None:
            self.prompt_token_counts.append(prompt)
        if total is not None:
            self._total_tokens.append(total)

    @property
    def max_prompt_tokens(self) -> int | None:
        """Largest reported prompt size, in tokens, or None when unavailable."""
        return max(self.prompt_token_counts) if self.prompt_token_counts else None

    @property
    def total_tokens(self) -> int | None:
        """Sum of reported total tokens, or None when unavailable."""
        return sum(self._total_tokens) if self._total_tokens else None


def load_pilot_config(path: Path) -> dict[str, Any]:
    """Load and validate the pilot YAML configuration."""
    with path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict) or config.get("experiment") != "pilot":
        raise ValueError("pilot config must be a mapping with experiment: pilot")
    if not isinstance(config.get("settings"), dict):
        raise ValueError("pilot config must define a settings mapping")
    required_settings = {
        "llm_provider", "backend_url", "temperature", "num_ctx",
        "selected_analysts", "max_debate_rounds", "max_risk_discuss_rounds",
    }
    missing_settings = required_settings - config["settings"].keys()
    if missing_settings:
        raise ValueError(f"settings missing: {', '.join(sorted(missing_settings))}")
    runs = config.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("pilot config must define a non-empty runs list")
    required = {"case_id", "ticker", "decision_date", "period", "seed"}
    for index, run in enumerate(runs):
        if not isinstance(run, dict) or required - run.keys():
            raise ValueError(f"runs[{index}] must define {', '.join(sorted(required))}")
        if not isinstance(run["seed"], int) or isinstance(run["seed"], bool) or run["seed"] < 0:
            raise ValueError(f"runs[{index}].seed must be a non-negative integer")
    return config


def generate_run_id(case_id: str, seed: int) -> str:
    """Create a filesystem-safe unique ID for one attempt of a pilot case."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", case_id).strip(".-_")
    if not slug:
        raise ValueError("case_id must contain at least one letter or digit")
    return f"{slug}-s{seed}-{uuid.uuid4().hex[:12]}"


def build_run_config(
    settings: dict[str, Any],
    seed: int,
    run_dir: Path,
    cache_dir: Path,
    base_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build TradingAgents config with per-run memory and project-local paths."""
    config = (DEFAULT_CONFIG if base_config is None else base_config).copy()
    config.update({
        "llm_provider": settings["llm_provider"],
        "backend_url": settings["backend_url"],
        "deep_think_llm": f"llama3.1-8k-s{seed}",
        "quick_think_llm": f"llama3.1-8k-s{seed}",
        "temperature": settings["temperature"],
        "max_debate_rounds": settings["max_debate_rounds"],
        "max_risk_discuss_rounds": settings["max_risk_discuss_rounds"],
        "memory_log_path": str(run_dir / "trading_memory.md"),
        "results_dir": str(run_dir),
        "data_cache_dir": str(cache_dir),
    })
    return config


def detect_machine() -> str:
    """Return the local GPU model when available, otherwise a platform label."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            check=True, capture_output=True, text=True, timeout=3,
        )
        gpu_name = result.stdout.strip().splitlines()
        if gpu_name and gpu_name[0]:
            return gpu_name[0]
    except (OSError, subprocess.SubprocessError):
        pass
    return platform.processor() or platform.machine() or platform.system()


def tradingagents_commit(repo_root: Path) -> str:
    """Read the checked-out TradingAgents commit without contacting the network."""
    result = subprocess.run(
        ["git", "-C", str(repo_root / "external" / "TradingAgents"), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def position_for_rating(rating: Any) -> float | None:
    """Map a documented five-tier rating to position; unknown values stay unmapped."""
    if isinstance(rating, Enum):
        rating = rating.value
    return RATING_POSITIONS.get(rating) if isinstance(rating, str) else None


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if hasattr(value, "content"):
        return {
            "type": type(value).__name__,
            "content": value.content,
            "additional_kwargs": getattr(value, "additional_kwargs", {}),
            "response_metadata": getattr(value, "response_metadata", {}),
        }
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"cannot serialize {type(value).__name__} to final_state JSON")


def _redact_error(exc: Exception) -> str:
    message = f"{type(exc).__name__}: {exc}"
    for pattern in _SECRET_PATTERNS:
        message = pattern.sub(lambda match: match.group(1) + "[REDACTED]" if match.lastindex else "[REDACTED]", message)
    return message[:2000]


def _status_for_exception(exc: Exception) -> str:
    """Keep recognizable timeouts distinct from other tool/runtime errors."""
    if isinstance(exc, TimeoutError) or "timeout" in type(exc).__name__.lower():
        return "timeout"
    return "tool_error"


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def run_pilot(
    config_path: Path,
    operator: str,
    machine: str | None = None,
    raw_root: Path | None = None,
    graph_factory: Callable[..., Any] | None = None,
    ta_commit: str | None = None,
) -> list[dict[str, Any]]:
    """Run configured pilot cases; append one status row per attempt."""
    if operator not in {"gav", "aya"}:
        raise ValueError("operator must be 'gav' or 'aya'")
    repo_root = Path(__file__).resolve().parents[1]
    raw_root = (raw_root or repo_root / "results" / "raw").resolve()
    cache_dir = (raw_root / "cache").resolve()
    run_root = (raw_root / "pilot").resolve()
    log_path = (raw_root / "pilot.jsonl").resolve()
    pilot_config = load_pilot_config(config_path)
    settings = pilot_config["settings"]
    run_specs = pilot_config["runs"]
    graph_factory = graph_factory or TradingAgentsGraph
    ta_commit = ta_commit or tradingagents_commit(repo_root)
    machine = machine or detect_machine()
    results: list[dict[str, Any]] = []

    for spec in run_specs:
        started_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        run_id = generate_run_id(spec["case_id"], spec["seed"])
        run_dir = run_root / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        memory_path = run_dir / "trading_memory.md"
        memory_path.touch(exist_ok=False)
        run_config = build_run_config(settings, spec["seed"], run_dir, cache_dir)
        recorder = TokenUsageRecorder()
        started = time.perf_counter()
        status = "tool_error"
        rating_raw = None
        position = None
        error = None
        final_state_path = None
        try:
            graph = graph_factory(
                selected_analysts=settings["selected_analysts"],
                config=run_config,
                callbacks=[recorder],
            )
            final_state, decision = graph.propagate(spec["ticker"], spec["decision_date"])
            rating_raw = decision.value if isinstance(decision, Enum) else str(decision)
            position = position_for_rating(decision)
            status = "ok" if position is not None else "parse_error"
            final_state_path = run_dir / "final_state.json"
            with final_state_path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(final_state, stream, ensure_ascii=False, indent=2, default=_json_default)
                stream.write("\n")
        except Exception as exc:
            status = _status_for_exception(exc)
            error = _redact_error(exc)
            logger.warning("Pilot run %s failed: %s", run_id, error)

        runtime_s = round(time.perf_counter() - started, 3)
        row = {
            "run_id": run_id,
            "case_id": spec["case_id"],
            "exp": "pilot",
            "ticker": spec["ticker"],
            "decision_date": spec["decision_date"],
            "period": spec["period"],
            "variant": settings.get("variant", "normal"),
            "config": settings.get("config", "full"),
            "seed": spec["seed"],
            "model": f"llama3.1-8k-s{spec['seed']}",
            "temperature": settings["temperature"],
            "num_ctx": settings["num_ctx"],
            "ta_commit": ta_commit,
            "operator": operator,
            "machine": machine,
            "status": status,
            "rating_raw": rating_raw,
            "position": position,
            "max_prompt_tokens": recorder.max_prompt_tokens,
            "prompt_token_counts": recorder.prompt_token_counts,
            "total_tokens": recorder.total_tokens,
            "runtime_s": runtime_s,
            "log_path": log_path.relative_to(repo_root).as_posix()
            if log_path.is_relative_to(repo_root) else str(log_path),
            "final_state_path": final_state_path.relative_to(repo_root).as_posix()
            if final_state_path and final_state_path.is_relative_to(repo_root) else None,
            "started_at": started_at,
        }
        if error is not None:
            row["error"] = error
        _append_jsonl(log_path, row)
        results.append(row)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Week 1 TradingAgents pilot grid")
    parser.add_argument("--config", type=Path, default=Path("configs/pilot.yaml"))
    parser.add_argument("--operator", choices=("gav", "aya"), required=True)
    parser.add_argument("--machine", help="Override automatic GPU/platform detection")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    rows = run_pilot(args.config, args.operator, machine=args.machine)
    logger.info("Logged %d pilot attempts (%d ok, %d failed)", len(rows),
                sum(row["status"] == "ok" for row in rows),
                sum(row["status"] != "ok" for row in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
