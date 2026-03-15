# Literature Review: Live Salmon Test for AI Scientists

## Research Area Overview

This research draws on two converging themes: (1) the "dead salmon" tradition in neuroscience—using known-null or known-process data to stress-test analytical pipelines—and (2) the rapidly emerging field of autonomous AI scientist systems. The "live salmon test" inverts the classic paradigm: instead of giving AI scientists null data (dead salmon), we provide data with a **known generating process** (live salmon) and evaluate whether they correctly recover it or produce spurious findings.

## Key Papers

### 1. Bennett et al. (2009) — "Neural Correlates of Interspecies Perspective Taking in the Post-Mortem Atlantic Salmon"
- **Authors**: Craig M. Bennett, Abigail A. Baird, Michael B. Miller, George L. Wolford
- **Year**: 2009 (poster, published 2010 in JSUR)
- **Key Contribution**: Demonstrated that standard fMRI analysis applied to a **dead salmon** yields "significant" brain activity (16 active voxels, p<0.001 uncorrected), illustrating the danger of not correcting for multiple comparisons.
- **Methodology**: Block-design fMRI with GLM analysis on a dead Atlantic salmon. Compared uncorrected vs. FDR/FWER-corrected results.
- **Key Finding**: With proper multiple comparisons correction (FDR, FWER), no voxels were significant even at relaxed thresholds (p=0.25).
- **Relevance**: The foundational inspiration for our "live salmon" concept. Establishes that analytical pipelines can produce plausible but completely spurious results.

### 2. Méloux et al. (2025) — "The Dead Salmons of AI Interpretability"
- **Authors**: Maxime Méloux, Giada Dirupo, François Portet, Maxime Peyrard
- **Year**: 2025 (arXiv: 2512.18792)
- **Key Contribution**: Extends the dead salmon concept to AI interpretability. Shows that feature attribution, probing, SAEs, and causal analyses produce plausible explanations for **randomly initialized** neural networks.
- **Methodology**: Applied correlation analysis and probing to randomized BERT on IMDb sentiment. Proposed statistical-causal reframing of interpretability.
- **Key Findings**: (1) PCA components of random BERT show spurious correlations with labels. (2) Probes achieve nontrivial accuracy on random networks. (3) Non-identifiability is the root cause of false discoveries.
- **Relevance**: Directly bridges the dead salmon concept to AI systems, providing the theoretical foundation for why AI scientists might produce spurious findings.

### 3. Lu et al. (2024) — "The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery"
- **Authors**: Chris Lu, Cong Lu, Robert Tjarko Lange, Jakob Foerster, Jeff Clune, David Ha
- **Year**: 2024 (arXiv: 2408.06292), Sakana AI
- **Key Contribution**: First comprehensive framework for fully automatic scientific discovery. AI generates ideas, writes code, runs experiments, writes papers, and reviews them—all for ~$15/paper.
- **Methodology**: LLM-based pipeline with idea generation, experiment templates (diffusion, language modeling, grokking), automated paper writing (LaTeX), and simulated peer review.
- **Datasets Used**: Custom experiment templates with generated data.
- **Results**: Automated reviewer achieves near-human accuracy (65% vs 66% balanced accuracy on ICLR 2022 data). Some papers exceed conference acceptance thresholds.
- **Code**: https://github.com/SakanaAI/AI-Scientist
- **Relevance**: The primary AI scientist system our "live salmon test" would evaluate. Its open-source nature makes it ideal for controlled testing.

### 4. Luo et al. (2025) — "The More You Automate, the Less You See: Hidden Pitfalls of AI Scientist Systems"
- **Authors**: Ziming Luo, Atoosa Kasirzadeh, Nihar B. Shah
- **Year**: 2025 (arXiv: 2509.08713), Carnegie Mellon University
- **Key Contribution**: Identifies four failure modes in AI scientist systems: inappropriate benchmark selection, data leakage, metric misuse, and post-hoc selection bias. Demonstrates these pitfalls in The AI Scientist v2 and Agent Laboratory.
- **Methodology**: Created fully synthetic tasks to avoid data contamination. Isolated each failure mode with controlled experiments. Audited decision-making traces.
- **Key Findings**: (1) AI scientists favor benchmarks with strong prior SOTA, not ones where their methods work best. (2) Both systems occasionally fabricate synthetic datasets without documenting it. (3) Internal reward mechanisms systematically favor experiments with strong test performance (post-hoc selection bias). (4) Paper-only review detects 55% of failures; log+code review detects 82%.
- **Code**: https://github.com/niharshah/AIScientistPitfalls
- **Relevance**: Most directly relevant methodology for our live salmon test. Their synthetic task approach parallels our known-DGP design. Their failure taxonomy provides the evaluation framework.

### 5. Beel et al. (2025) — "Evaluating Sakana's AI Scientist"
- **Authors**: Joeran Beel, Min-Yen Kan, Moritz Baumgart
- **Year**: 2025 (arXiv: 2502.14297)
- **Key Contribution**: First comprehensive independent evaluation of Sakana's AI Scientist through direct experimentation.
- **Key Findings**: (1) 42% of experiments failed due to coding errors. (2) Literature review is inadequate (median 5 citations, mostly outdated). (3) Hallucinated numerical results in manuscripts. (4) Quality comparable to "unmotivated undergraduate." (5) Despite failures, produces complete papers at $6-$15 each in 3.5 hours.
- **Relevance**: Establishes baseline expectations for AI Scientist output quality. Shows current systems are far from reliable but technically impressive.

### 6. Zhu et al. (2025) — "AI Scientists Fail Without Strong Implementation Capability"
- **Authors**: Minjun Zhu, Qiujie Xie, Yixuan Weng, et al.
- **Year**: 2025 (arXiv: 2506.01372), Westlake University
- **Key Contribution**: Position paper arguing the fundamental bottleneck for AI Scientists is implementation capability, not idea generation. Evaluated 28 papers from 5 AI scientist systems.
- **Key Findings**: (1) LLMs generate highly novel ideas but execution is poor (Claude 3.5 Sonnet: 1.8% on PaperBench). (2) The "implementation gap" between idea quality and verification quality is the key barrier. (3) Current systems lack execution capabilities for rigorous experiments.
- **Relevance**: Suggests our live salmon test should focus on whether AI scientists correctly implement the analytical pipeline, not just whether they generate reasonable hypotheses.

### 7. Starace et al. (2025) — "PaperBench: Evaluating AI's Ability to Replicate AI Research"
- **Authors**: Giulio Starace, Oliver Jaffe, et al. (OpenAI)
- **Year**: 2025 (arXiv: 2504.01848)
- **Key Contribution**: Benchmark with 20 ICML 2024 papers decomposed into 8,316 individually gradable sub-tasks. Best agent (Claude 3.5 Sonnet) achieves only 21% replication score.
- **Relevance**: Provides quantitative evidence of the implementation gap. Suggests AI scientists will struggle with the analytical rigor needed to correctly recover our known DGP.

### 8. Gu et al. (2024) — "BLADE: Benchmarking Language Model Agents for Data-Driven Science"
- **Authors**: Ken Gu, Ruoxi Shang, et al.
- **Year**: 2024 (arXiv: 2408.09667)
- **Key Contribution**: Benchmark for evaluating agents on open-ended research questions with 12 datasets and ground truth from expert data scientists. Agents capable of interacting with data show improved but non-optimal analytical diversity.
- **Relevance**: Closest existing benchmark to our live salmon concept. Provides methodology for evaluating whether AI agents make appropriate analytical decisions.

### 9. Si et al. (2024) — "Can LLMs Generate Novel Research Ideas?"
- **Authors**: Chenglei Si, et al.
- **Year**: 2024 (arXiv: 2409.04109)
- **Key Contribution**: Large-scale study with 100+ NLP researchers. LLM-generated ideas rated as more novel than human expert ideas but weaker on feasibility.
- **Relevance**: Establishes that idea generation is not the bottleneck; implementation and verification are.

### 10. Eklund et al. (2016) — "Cluster Failure: Why fMRI Inferences for Spatial Extent Have Inflated False-Positive Rates"
- **Authors**: Anders Eklund, Thomas E. Nichols, Hans Knutsson
- **Year**: 2016 (PNAS, arXiv: 1511.01863)
- **Key Contribution**: Showed that widely used fMRI statistical software (SPM, FSL, AFNI) produced inflated false-positive rates (up to 70% instead of expected 5%), potentially invalidating ~40,000 fMRI studies.
- **Relevance**: Demonstrates at scale what Bennett's dead salmon showed in principle—standard analytical pipelines can systematically produce false positives. Provides precedent for our systematic evaluation approach.

### 11. Emmert-Streib & Dehmer (2019) — "Large-Scale Simultaneous Inference with Hypothesis Testing: Multiple Testing Procedures in Practice"
- **Year**: 2019
- **Key Contribution**: Comprehensive review of multiple testing procedures (FWER, FDR control), emphasizing methods for correlated data.
- **Relevance**: Provides the statistical methodology framework for evaluating whether AI scientists properly handle multiple comparisons.

## Common Methodologies in Evaluating AI Scientists

1. **Synthetic/Controlled Tasks**: Creating novel tasks outside training data to avoid contamination (Luo et al., 2025)
2. **Trace Auditing**: Examining logs and code, not just final papers (Luo et al., 2025)
3. **Rubric-Based Evaluation**: Hierarchical decomposition of tasks into gradable sub-tasks (Starace et al., 2025)
4. **Automated Review**: Using LLMs to evaluate generated papers (Lu et al., 2024; Weng et al., 2024)
5. **Human Expert Comparison**: Comparing AI output to human researcher baselines (Si et al., 2024; Starace et al., 2025)

## Standard Baselines

- **The AI Scientist v1/v2** (Sakana AI): End-to-end automated research
- **Agent Laboratory**: LLM research assistant with human-in-the-loop
- **CycleResearcher**: Automated research with iterative review feedback
- **Human researchers**: ML PhD students and expert data scientists

## Evaluation Metrics

- **Replication score**: Fraction of rubric items correctly completed (PaperBench)
- **Review score**: Simulated peer review ratings (1-10 scale)
- **Pitfall detection rate**: Binary classification of methodological failures
- **Analytical decision diversity**: Variety of valid approaches attempted (BLADE)
- **Ground truth recovery**: Whether correct DGP/model is identified (our approach)

## Gaps and Opportunities

1. **No "live salmon" benchmark exists**: Current evaluations test either open-ended tasks (no ground truth) or replication tasks (known answer). A controlled DGP recovery task is novel.
2. **Lack of statistical rigor evaluation**: Existing evaluations focus on paper quality, not whether the statistical analysis is correct.
3. **Multiple comparisons not tested**: No benchmark specifically tests whether AI scientists handle multiple hypothesis testing correctly.
4. **Cross-system comparison limited**: Most evaluations test one system; comparative studies are rare.
5. **Known DGP evaluation**: Testing whether AI scientists can recover a known data generating process has not been systematically studied.

## Recommendations for Our Experiment

### Recommended Datasets
- **Primary**: Custom "live salmon" synthetic dataset with known DGP (generated)
- **Control**: "Dead salmon" null dataset with no signal (generated)
- **Validation**: BLADE benchmark datasets (for comparison with existing results)

### Recommended Baselines
- The AI Scientist (Sakana AI) — primary target system
- Agent Laboratory — secondary target
- Human data scientist analysis — gold standard

### Recommended Metrics
1. **True model recovery**: Can the AI scientist identify the correct features and functional form?
2. **False discovery rate**: Does it report spurious features/relationships?
3. **Multiple comparisons handling**: Does it apply proper corrections?
4. **Statistical significance**: Are reported p-values/confidence intervals valid?
5. **Reproducibility**: Do results hold across random seeds?

### Methodological Considerations
- Use fully synthetic data to avoid contamination (per Luo et al., 2025)
- Audit both final papers AND intermediate traces/code
- Test multiple AI scientist systems for comparison
- Include known non-linearities and interaction effects to test analytical depth
- Vary signal-to-noise ratio to test sensitivity
