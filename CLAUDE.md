# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

PIDSMaker is a framework for building and evaluating **Provenance-based Intrusion Detection Systems (PIDSs)**. It processes raw system audit logs (from PostgreSQL), constructs provenance graphs, trains GNN-based anomaly detection models, and evaluates them on known attack scenarios.

Supported systems: `velox`, `orthrus`, `nodlink`, `threatrace`, `kairos`, `rcaid`, `flash`, `magic`

Supported datasets: DARPA TC datasets (CLEARSCOPE/CADETS/THEIA E3/E5), OptC, PROVATTACK variants

## Running the Code

```bash
# Standard run (trains + infers + evaluates)
python pidsmaker/main.py <system> <dataset>

# With Weights & Biases
python pidsmaker/main.py kairos CADETS_E3 --wandb

# Background run
./run.sh kairos CADETS_E3

# Override config params from CLI
python pidsmaker/main.py kairos CADETS_E3 --detection.gnn_training.lr=0.0001

# Hyperparameter tuning
./run.sh kairos CADETS_E3 --tuning_mode=hyperparameters
```

## Train Once, Test Multiple (PROVATTACK Flow)

```bash
# Step 1: Create unified DB (once)
python -m dataset_preprocessing.provattack.create_database flash training_full

# Step 2: Train on benign data
python pidsmaker/main.py flash training_full

# Step 3: Inference on each attack (reuses trained model via hash)
python pidsmaker/main.py flash training_full_aa23_341a
python pidsmaker/main.py flash training_full_alphvblackcat
```

## Pipeline Architecture

The 9-stage pipeline in `pidsmaker/main.py` runs stages in order. Each stage is skipped if already complete (marked by `done.txt`). Outputs are stored at `artifacts/<task>/<config_hash>/<dataset>/`.

```
Raw Events (PostgreSQL)
  → build_graphs       preprocessing/build_graphs.py       NetworkX graphs per day
  → transformation     preprocessing/transformation.py     Filter/modify graphs
  → feat_training      featurization/feat_training.py      Node embeddings (w2v, doc2vec, etc.)
  → feat_inference     featurization/feat_inference.py     Edge embeddings (src+edge+dst)
  → graph_preprocessing detection/graph_preprocessing.py  Batch into PyTorch temporal data
  → gnn_training       detection/gnn_training.py           Train TGN+GNN model
  → gnn_inference      detection/gnn_inference.py          Per-edge anomaly scores
  → evaluation         detection/evaluation.py             Node-level labels + metrics
  → tracing            triage/tracing.py                   Attack investigation
```

**Content-addressed caching**: each stage path includes a hash of relevant config params. Stages with identical config reuse existing outputs — this is how "train once" works across multiple attack datasets.

## Configuration System

- YAML configs per system: `config/<system>.yml` (e.g., `config/kairos.yml`)
- Configs use `_include_yml` for inheritance
- Loaded via YACS in `pidsmaker/config/pipeline.py`
- Dataset defaults (file splits, DB names, attack windows) are hardcoded in `pidsmaker/config/config.py`
- `PROVATTACK_DATASETS` list in `config.py` controls which datasets are PROVATTACK variants

## Key Files

| File | Role |
|------|------|
| `pidsmaker/main.py` | Pipeline orchestrator, task dependency management |
| `pidsmaker/config/config.py` | Dataset configs (DB names, file splits, attack windows, node/edge counts) |
| `pidsmaker/config/pipeline.py` | YACS config loading, CLI arg parsing, sweep setup |
| `pidsmaker/factory.py` | Builds Model from encoder + objectives based on config |
| `pidsmaker/model.py` | `Model` class: encoder + objectives, training/inference forward pass |
| `pidsmaker/tgn.py` | Temporal Graph Network (TGN) memory module |
| `pidsmaker/utils/utils.py` | DB connection, graph utils, node tokenization, split management |
| `pidsmaker/utils/dataset_utils.py` | `rel2id`, `ntype2id` mappings per dataset; edge type definitions |
| `dataset_preprocessing/provattack/` | Scripts to preprocess and load PROVATTACK datasets |

## Model Architecture

Built by `factory.py`:
- **Encoder**: TGN (temporal memory) + GNN layers (GraphAttention or GraphSAGE), configured via `detection.gnn_training.encoder`
- **Objectives/Decoders**: Edge type prediction, node prediction, hybrid — configured via `detection.gnn_training.decoder`
- Models saved to: `artifacts/detection/gnn_training/<hash>/<dataset>/trained_models/model_epoch_N.pt`

## Linting

```bash
ruff check pidsmaker/
ruff format pidsmaker/
```
(line length: 100, configured in `pyproject.toml`)

## Change Logging

After completing any task that modifies files, append a summary to `CHANGES.md` with:
- Date (YYYY-MM-DD)
- What changed and why (1-3 sentences)
- Files affected
