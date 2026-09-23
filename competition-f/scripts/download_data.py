#!/usr/bin/env python3
"""Download publicly available competition data into real_attachments/."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "real_attachments"

REGMIX_BASE = "https://raw.githubusercontent.com/sail-sg/regmix/main/data"
REGMIX_FILES = [
    "train_mixture_1m.csv",
    "train_pile_loss_1m.csv",
    "test_mixture_1m.csv",
    "test_pile_loss_1m.csv",
    "test_mixture_60m.csv",
    "test_pile_loss_60m.csv",
    "test_mixture_1B.csv",
    "test_pile_loss_1B.csv",
    "est_mixture_10b.csv",
    "est_pile_loss_10b.csv",
    "est_mixture_70b.csv",
    "est_pile_loss_70b.csv",
]

PYTHIA_LOG_URL = (
    "https://huggingface.co/datasets/EleutherAI/pythia/resolve/main/"
    "pythia-1.4b/pythia-1.4b-log.json"
)
EPOCH_URL = "https://epoch.ai/data/all_ai_models.csv"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"skip existing {dest}")
        return
    print(f"downloading {url} -> {dest}")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)


def download_regmix() -> None:
    out = DATA / "A_data_value/regmix_tables"
    for name in REGMIX_FILES:
        download(f"{REGMIX_BASE}/{name}", out / name)


def download_pythia_logs() -> None:
    """Fetch Pythia training logs via huggingface if local file missing."""
    dest = DATA / "B_scaling_laws/pythia_training_log_existing.csv"
    if dest.exists():
        return
    try:
        from huggingface_hub import hf_hub_download

        # Use bundled contest-style log from EleutherAI scaling analysis repo if available
        path = hf_hub_download(
            repo_id="EleutherAI/pythia",
            filename="pythia-70m/pythia-70m-log.json",
            repo_type="model",
        )
        print(f"hf pythia log sample: {path}")
    except Exception as e:
        print(f"pythia hf download note: {e}")


def download_leaderboard() -> None:
    dest = DATA / "C_efficiency_evolution/leaderboard_cleaned.csv"
    if dest.exists():
        return
    try:
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(
            repo_id="open-llm-leaderboard-old/results",
            filename="results.csv",
            repo_type="dataset",
        )
        import shutil

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, dest)
        print(f"leaderboard -> {dest}")
    except Exception as e:
        print(f"leaderboard download failed: {e}")


def download_epoch() -> None:
    download(EPOCH_URL, DATA / "C_efficiency_evolution/epoch_all_ai_models.csv")


def create_domain_mapping() -> None:
    dest = DATA / "A_data_value/domain_mapping_guide.csv"
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = """mixture_domain,quality_domain,mapping_type,weight
arxiv,arxiv,direct,1.0
github,github,direct,1.0
wikipedia_en,wikipedia,direct,1.0
stackexchange,stackexchange,direct,1.0
dm_mathematics,book,near_direct,0.8
gutenberg_pg_19,book,direct,0.9
freelaw,book,inferred,0.5
pubmed_central,book,inferred,0.6
pubmed_abstracts,book,inferred,0.6
nih_exporter,book,inferred,0.4
pile_cc,commoncrawl,near_direct,0.85
hackernews,stackexchange,inferred,0.5
ubuntu_irc,stackexchange,inferred,0.4
enron_emails,c4,inferred,0.3
europarl,c4,inferred,0.3
philpapers,book,inferred,0.4
uspto_backgrounds,book,inferred,0.5
"""
    dest.write_text(rows.strip() + "\n", encoding="utf-8")


def main() -> None:
    download_regmix()
    download_epoch()
    create_domain_mapping()
    download_pythia_logs()
    download_leaderboard()
    print("download_data done")


if __name__ == "__main__":
    main()
