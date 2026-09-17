#!/usr/bin/env python3
"""
generate-proposal eval runner.

Requires:
  pip install anthropic
  ANTHROPIC_API_KEY set (or an `ant auth login` profile) in this environment.
  .cache/<portal_id>.json for every ID in inputs.json — produced by the
  fetch step described in FETCH.md (run inside a Claude Code session with
  the Client_Command_-_NEW MCP tools).

Writes one JSON file per trial plus a summary to results/ (gitignored —
trial files quote real client content via the drafts and judge rationale).
"""

import json
import random
import re
import sys
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
CACHE_DIR = HERE / ".cache"
RESULTS_DIR = HERE / "results"

MODEL_A_ID = "claude-opus-4-7"
MODEL_B_ID = "claude-sonnet-5"
JUDGE_MODEL_ID = "claude-opus-5"

GENERATION_SYSTEM_PROMPT = (HERE / "prompt.md").read_text().split("```\n", 1)[1].rsplit("```", 1)[0]

JUDGE_INSTRUCTIONS = (HERE / "rubric.md").read_text().split("```\n", 1)[1].rsplit("```", 1)[0]


def load_inputs():
    manifest = json.loads((HERE / "inputs.json").read_text())
    inputs = []
    for portal_id in manifest["portal_ids"]:
        cache_file = CACHE_DIR / f"{portal_id}.json"
        if not cache_file.exists():
            print(f"skip {portal_id}: no cached input (see FETCH.md)", file=sys.stderr)
            continue
        inputs.append((portal_id, json.loads(cache_file.read_text())))
    return inputs


def draft_proposal(client: anthropic.Anthropic, model: str, portal_input: dict) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=GENERATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(portal_input, indent=2)}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def judge_pair(client: anthropic.Anthropic, portal_input: dict, draft_a: str, draft_b: str) -> dict:
    user_content = (
        f"Client context:\n{json.dumps(portal_input, indent=2)}\n\n"
        f"--- Draft A ---\n{draft_a}\n\n"
        f"--- Draft B ---\n{draft_b}\n\n"
        "Respond with only a JSON object: "
        '{"winner": "A"|"B"|"tie", "rationale": "...", "confidence": "low"|"medium"|"high"}'
    )
    response = client.messages.create(
        model=JUDGE_MODEL_ID,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=JUDGE_INSTRUCTIONS,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"judge did not return parseable JSON: {text!r}")
    return json.loads(match.group(0))


def run():
    client = anthropic.Anthropic()
    RESULTS_DIR.mkdir(exist_ok=True)
    inputs = load_inputs()
    if not inputs:
        print("no cached inputs found — nothing to run. See FETCH.md.", file=sys.stderr)
        return

    trials = []
    for portal_id, portal_input in inputs:
        draft_opus_4_7 = draft_proposal(client, MODEL_A_ID, portal_input)
        draft_sonnet_5 = draft_proposal(client, MODEL_B_ID, portal_input)

        # Blind, randomized A/B labeling — independent of model identity.
        if random.random() < 0.5:
            label_to_model = {"A": ("opus-4-7", draft_opus_4_7), "B": ("sonnet-5", draft_sonnet_5)}
        else:
            label_to_model = {"A": ("sonnet-5", draft_sonnet_5), "B": ("opus-4-7", draft_opus_4_7)}

        verdict = judge_pair(client, portal_input, label_to_model["A"][1], label_to_model["B"][1])
        winner_label = verdict.get("winner")
        winner_model = label_to_model[winner_label][0] if winner_label in ("A", "B") else "tie"

        trial = {
            "portal_id": portal_id,
            "label_to_model": {k: v[0] for k, v in label_to_model.items()},
            "verdict": verdict,
            "winner_model": winner_model,
            "draft_opus_4_7": draft_opus_4_7,
            "draft_sonnet_5": draft_sonnet_5,
        }
        trials.append(trial)
        (RESULTS_DIR / f"{portal_id}.json").write_text(json.dumps(trial, indent=2))
        print(f"{portal_id}: winner={winner_model} confidence={verdict.get('confidence')}")

    wins = {"opus-4-7": 0.0, "sonnet-5": 0.0}
    for t in trials:
        if t["winner_model"] == "tie":
            wins["opus-4-7"] += 0.5
            wins["sonnet-5"] += 0.5
        else:
            wins[t["winner_model"]] += 1

    summary = {"n_trials": len(trials), "wins": wins}
    (RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
