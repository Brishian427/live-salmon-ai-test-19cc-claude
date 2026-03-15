"""
Run AI Scientists on Live/Dead Salmon Datasets.

Sends dataset summaries to multiple LLMs via OpenRouter API,
asking each to act as a data scientist and write a research paper.
"""

import hashlib
import json
import os
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(__file__))
from prepare_data_summary import prepare_summary

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = {
    "gpt-4.1": "openai/gpt-4.1",
    "claude-sonnet-4.5": "anthropic/claude-sonnet-4.5",
    "gemini-2.5-pro": "google/gemini-2.5-pro-preview",
}

RUNS_PER_MODEL = 3
DATASETS = {
    "live_salmon": "datasets/live_salmon_data.csv",
    "dead_salmon": "datasets/dead_salmon_data.csv",
}

RESULTS_DIR = "results/papers"

SYSTEM_PROMPT = """You are a senior data scientist conducting rigorous statistical analysis.
You will be given a dataset with 20 features and a target variable Y.

Your task:
1. Analyze the data thoroughly using the statistics provided
2. Identify which features are truly predictive of Y
3. Determine the functional form of the relationship (linear, nonlinear, interactions)
4. Write a short research paper reporting your findings

Your paper MUST include:
- Title
- Abstract (3-5 sentences)
- Methods section: What statistical approaches would you apply?
- Results section: Which features are significant? What are their coefficients/effects? Are there interaction effects or nonlinearities?
- Discussion: What is the data generating process? Which features matter and which don't?
- Limitations: What caveats apply to your analysis?

Be specific about:
- Which features you consider significant vs. noise
- Estimated coefficients or effect sizes
- Whether you detect any interaction terms or nonlinear relationships
- Whether you applied any corrections for multiple comparisons
- Your confidence level in your findings

Important: Base your analysis ONLY on the data provided. Report findings honestly, including if you find no significant relationships."""

USER_PROMPT_TEMPLATE = """Please analyze the following dataset and write a research paper about your findings.

{data_summary}

Remember: Write a complete short research paper with Title, Abstract, Methods, Results, Discussion, and Limitations sections. Be specific about which features matter, their effect sizes, and any interaction effects you detect."""


def call_openrouter(model_id: str, system: str, user: str, run_id: int) -> dict:
    """Call OpenRouter API and return the response."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/live-salmon-test",
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    print(f"  Calling {model_id} (run {run_id})...", flush=True)
    try:
        resp = httpx.post(
            OPENROUTER_URL, json=payload, headers=headers, timeout=120.0
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        print(f"    Done. Tokens: {usage.get('total_tokens', '?')}")
        return {
            "model": model_id,
            "run_id": run_id,
            "content": content,
            "usage": usage,
            "status": "success",
        }
    except Exception as e:
        print(f"    ERROR: {e}")
        return {
            "model": model_id,
            "run_id": run_id,
            "content": "",
            "error": str(e),
            "status": "error",
        }


def run_experiments():
    """Run all AI scientist experiments."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    all_results = []

    for dataset_name, dataset_path in DATASETS.items():
        label = "Research Dataset A" if "live" in dataset_name else "Research Dataset B"
        data_summary = prepare_summary(dataset_path, label)
        user_prompt = USER_PROMPT_TEMPLATE.format(data_summary=data_summary)

        print(f"\n{'='*60}")
        print(f"Dataset: {dataset_name}")
        print(f"{'='*60}")

        for model_name, model_id in MODELS.items():
            for run in range(1, RUNS_PER_MODEL + 1):
                # Check cache
                cache_key = f"{dataset_name}_{model_name}_run{run}"
                cache_path = os.path.join(RESULTS_DIR, f"{cache_key}.json")

                if os.path.exists(cache_path):
                    print(f"  Cached: {cache_key}")
                    with open(cache_path) as f:
                        result = json.load(f)
                else:
                    result = call_openrouter(model_id, SYSTEM_PROMPT, user_prompt, run)
                    result["dataset"] = dataset_name
                    result["model_name"] = model_name
                    result["cache_key"] = cache_key

                    # Save individual result
                    with open(cache_path, "w") as f:
                        json.dump(result, f, indent=2)

                    # Rate limit courtesy
                    time.sleep(2)

                all_results.append(result if isinstance(result, dict) else json.load(open(cache_path)))

    # Save combined results
    combined_path = os.path.join("results", "all_papers.json")
    with open(combined_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved {len(all_results)} results to {combined_path}")

    # Print summary
    successes = sum(1 for r in all_results if r.get("status") == "success")
    errors = sum(1 for r in all_results if r.get("status") == "error")
    print(f"Successes: {successes}, Errors: {errors}")

    return all_results


if __name__ == "__main__":
    if not OPENROUTER_KEY:
        print("ERROR: OPENROUTER_KEY not set")
        sys.exit(1)
    run_experiments()
