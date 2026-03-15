# Cloned Repositories

## Repo 1: AI-Scientist (Sakana AI)
- **URL**: https://github.com/SakanaAI/AI-Scientist
- **Purpose**: The primary AI scientist system to evaluate. End-to-end automated research: idea generation → experiments → paper writing → review.
- **Location**: code/AI-Scientist/
- **Key files**:
  - `launch_scientist.py` — Main entry point
  - `ai_scientist/generate_ideas.py` — Idea generation
  - `ai_scientist/perform_experiments.py` — Experiment execution
  - `ai_scientist/perform_writeup.py` — Paper writing
  - `ai_scientist/perform_review.py` — Automated review
  - `templates/` — Experiment templates (nanoGPT, diffusion, grokking)
- **Requirements**: Linux, NVIDIA GPU, Python 3.11, texlive-full, LLM API keys
- **Notes**: Produces papers at ~$15 each. We can adapt templates to create a "live salmon" experiment template with our synthetic dataset.

## Repo 2: AIScientistPitfalls (CMU)
- **URL**: https://github.com/niharshah/AIScientistPitfalls
- **Purpose**: Framework for detecting methodological pitfalls in AI scientist systems. Accompanies "The More You Automate, the Less You See" paper.
- **Location**: code/AIScientistPitfalls/
- **Key files**:
  - `pitfall_detection/pitfall_detection.py` — Main detection pipeline
  - `pitfall_detection/BenchmarkIssue/` — Benchmark selection detection
  - `pitfall_detection/DataLeakage/` — Data leakage detection
  - `pitfall_detection/MetricMisuse/` — Metric misuse detection
  - `pitfall_detection/PostHocSelection/` — Post-hoc selection bias detection
  - `SPR Task/` — Synthetic task for evaluation
- **Requirements**: Python 3.8+, LLM API keys
- **Notes**: Their synthetic task approach directly parallels our "live salmon" design. Their pitfall taxonomy can be adapted to evaluate whether AI scientists correctly handle our known DGP.
