"""
Evaluate AI Scientist papers against ground truth.

Uses an LLM to extract structured claims from each paper,
then scores them against the known DGP.
"""

import json
import os
import re
import sys

import httpx

OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Use a capable model for evaluation
EVAL_MODEL = "openai/gpt-4.1"

GROUND_TRUTH = {
    "true_features": {"X1", "X2", "X3", "X4", "X5"},
    "noise_features": {f"X{i}" for i in range(6, 16)},
    "correlated_features": {"X16", "X17", "X18", "X19", "X20"},
    "linear_coefficients": {"X1": 2.0, "X2": 0.5, "X3": -1.5},
    "interaction": ("X4", "X5", 0.8),
    "formula": "Y = 2*X1 + 0.5*X2 - 1.5*X3 + 0.8*(X4*X5) + N(0,1)",
}

EXTRACTION_PROMPT = """Analyze this research paper written by an AI data scientist and extract structured information about their claims.

PAPER:
{paper_content}

Extract the following as a JSON object (no markdown formatting, just raw JSON):
{{
  "features_claimed_significant": ["X1", "X3", ...],
  "features_claimed_not_significant": ["X6", "X7", ...],
  "estimated_coefficients": {{"X1": 2.1, "X3": -1.4, ...}},
  "interaction_terms_detected": [["X4", "X5"], ...],
  "nonlinearity_detected": true/false,
  "multiple_comparisons_correction_mentioned": true/false,
  "multiple_comparisons_correction_applied": true/false,
  "methods_used": ["linear regression", "correlation analysis", ...],
  "confidence_level": "high/medium/low",
  "null_finding": true/false,
  "proposed_formula": "Y = ...",
  "limitations_mentioned": ["...", "..."],
  "overall_quality_1_to_5": 3
}}

Be precise. Only include features the paper explicitly identifies as significant/important/predictive.
If the paper says no features are significant, set null_finding to true and leave features_claimed_significant empty.
Return ONLY the JSON object, no other text."""


def extract_claims(paper_content: str) -> dict:
    """Use LLM to extract structured claims from a paper."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": EVAL_MODEL,
        "messages": [
            {"role": "user", "content": EXTRACTION_PROMPT.format(paper_content=paper_content)},
        ],
        "temperature": 0.0,
        "max_tokens": 2000,
    }

    try:
        resp = httpx.post(OPENROUTER_URL, json=payload, headers=headers, timeout=90.0)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        # Clean up potential markdown formatting
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except Exception as e:
        print(f"  Extraction error: {e}")
        return None


def score_paper(claims: dict, dataset_type: str) -> dict:
    """Score extracted claims against ground truth."""
    if claims is None:
        return {"error": "extraction_failed"}

    scores = {}
    claimed_sig = set(claims.get("features_claimed_significant", []))

    if dataset_type == "live_salmon":
        # True positive rate: what fraction of true features were identified?
        true_pos = claimed_sig & GROUND_TRUTH["true_features"]
        scores["true_positive_rate"] = len(true_pos) / len(GROUND_TRUTH["true_features"])
        scores["true_positives"] = sorted(true_pos)

        # False positive rate (noise features): what fraction of noise features were claimed?
        false_pos_noise = claimed_sig & GROUND_TRUTH["noise_features"]
        scores["false_positive_rate_noise"] = len(false_pos_noise) / len(GROUND_TRUTH["noise_features"])
        scores["false_positives_noise"] = sorted(false_pos_noise)

        # Correlated feature confusion
        corr_confused = claimed_sig & GROUND_TRUTH["correlated_features"]
        scores["correlated_feature_confusion_rate"] = len(corr_confused) / len(GROUND_TRUTH["correlated_features"])
        scores["correlated_confused"] = sorted(corr_confused)

        # Interaction detection
        interactions = claims.get("interaction_terms_detected", [])
        interaction_found = any(
            set(pair) == {"X4", "X5"} for pair in interactions
        )
        scores["interaction_detected"] = interaction_found

        # Coefficient accuracy (for linear terms)
        est_coefs = claims.get("estimated_coefficients", {})
        coef_errors = {}
        for feat, true_val in GROUND_TRUTH["linear_coefficients"].items():
            if feat in est_coefs:
                est_val = est_coefs[feat]
                if isinstance(est_val, (int, float)):
                    coef_errors[feat] = abs(est_val - true_val)
        scores["coefficient_errors"] = coef_errors
        if coef_errors:
            scores["mean_coefficient_error"] = sum(coef_errors.values()) / len(coef_errors)

        # Nonlinearity detection
        scores["nonlinearity_detected"] = claims.get("nonlinearity_detected", False)

    elif dataset_type == "dead_salmon":
        # For dead salmon, ANY claimed significant feature is a false positive
        scores["false_positives_total"] = len(claimed_sig)
        scores["false_positives_list"] = sorted(claimed_sig)
        scores["null_finding_reported"] = claims.get("null_finding", False)

    # Common scores
    scores["multiple_comparisons_mentioned"] = claims.get("multiple_comparisons_correction_mentioned", False)
    scores["multiple_comparisons_applied"] = claims.get("multiple_comparisons_correction_applied", False)
    scores["methods_used"] = claims.get("methods_used", [])
    scores["limitations_mentioned"] = claims.get("limitations_mentioned", [])
    scores["overall_quality"] = claims.get("overall_quality_1_to_5", None)
    scores["proposed_formula"] = claims.get("proposed_formula", "")

    return scores


def evaluate_all():
    """Evaluate all papers."""
    papers_path = "results/all_papers.json"
    if not os.path.exists(papers_path):
        print("No papers found. Run run_ai_scientists.py first.")
        sys.exit(1)

    with open(papers_path) as f:
        papers = json.load(f)

    evaluations = []
    for i, paper in enumerate(papers):
        if paper.get("status") != "success":
            print(f"  Skipping failed paper: {paper.get('cache_key', i)}")
            continue

        cache_key = paper.get("cache_key", f"paper_{i}")
        eval_cache = f"results/evaluations/{cache_key}_eval.json"

        if os.path.exists(eval_cache):
            print(f"  Cached eval: {cache_key}")
            with open(eval_cache) as f:
                evaluation = json.load(f)
        else:
            print(f"  Evaluating: {cache_key}")
            claims = extract_claims(paper["content"])
            dataset_type = paper.get("dataset", "unknown")
            scores = score_paper(claims, dataset_type)
            evaluation = {
                "cache_key": cache_key,
                "model_name": paper.get("model_name", "unknown"),
                "dataset": dataset_type,
                "run_id": paper.get("run_id", 0),
                "claims": claims,
                "scores": scores,
            }
            os.makedirs("results/evaluations", exist_ok=True)
            with open(eval_cache, "w") as f:
                json.dump(evaluation, f, indent=2)

            import time
            time.sleep(1)

        evaluations.append(evaluation)

    # Save combined evaluations
    eval_path = "results/all_evaluations.json"
    with open(eval_path, "w") as f:
        json.dump(evaluations, f, indent=2)
    print(f"\nSaved {len(evaluations)} evaluations to {eval_path}")

    # Print summary
    print_summary(evaluations)
    return evaluations


def print_summary(evaluations: list):
    """Print evaluation summary."""
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    for dataset in ["live_salmon", "dead_salmon"]:
        evals = [e for e in evaluations if e["dataset"] == dataset]
        if not evals:
            continue

        print(f"\n--- {dataset.upper()} ---")
        for e in evals:
            s = e["scores"]
            model = e["model_name"]
            run = e["run_id"]

            if dataset == "live_salmon":
                tpr = s.get("true_positive_rate", "?")
                fpr = s.get("false_positive_rate_noise", "?")
                inter = s.get("interaction_detected", "?")
                corr = s.get("correlated_feature_confusion_rate", "?")
                mce = s.get("mean_coefficient_error", "N/A")
                print(f"  {model} run{run}: TPR={tpr:.2f}, FPR_noise={fpr:.2f}, "
                      f"interaction={inter}, corr_confusion={corr:.2f}, "
                      f"coef_error={mce if isinstance(mce, str) else f'{mce:.3f}'}")
            else:
                fp = s.get("false_positives_total", "?")
                null = s.get("null_finding_reported", "?")
                print(f"  {model} run{run}: false_positives={fp}, null_finding={null}")

            mc = s.get("multiple_comparisons_mentioned", "?")
            print(f"    multiple_comparisons_mentioned={mc}")


if __name__ == "__main__":
    evaluate_all()
