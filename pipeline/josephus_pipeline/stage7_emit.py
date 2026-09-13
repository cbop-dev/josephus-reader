"""Stage 7: Emission of public JSON datasets into app/public/data/ and static/data/."""

from __future__ import annotations

import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from .config import Manifest, BUILD_DIR, REPO_ROOT


def get_greek_bucket(text: str) -> str:
    if not text:
        return "other"
    norm = unicodedata.normalize("NFD", text)
    first_chars = [c for c in norm if unicodedata.category(c) != "Mn"]
    if not first_chars:
        return "other"
    ch = first_chars[0].lower()
    greek_buckets = {
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
        'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta',
        'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu',
        'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 'π': 'pi',
        'ρ': 'rho', 'σ': 'sigma', 'ς': 'sigma', 'τ': 'tau',
        'υ': 'upsilon', 'φ': 'phi', 'χ': 'chi', 'ψ': 'psi',
        'ω': 'omega'
    }
    return greek_buckets.get(ch, "other")


def save_merged_json(file_path: Path, new_data: dict):
    existing = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    existing.update(new_data)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False)


def run_stage7(manifest: Manifest) -> dict:
    work_id = manifest.work_id
    stage1_file = BUILD_DIR / "stage1" / work_id / f"{work_id}.json"
    stage4_file = BUILD_DIR / "stage4" / work_id / "morph_map.json"
    stage5_file = BUILD_DIR / "stage5" / work_id / "lsj_map.json"
    stage6_file = BUILD_DIR / "stage6" / work_id / "concordance.json"

    if not stage1_file.exists():
        raise FileNotFoundError(f"Stage 1 output missing for {work_id}")

    with open(stage1_file, "r", encoding="utf-8") as f:
        work_data = json.load(f)

    morph_map = {}
    if stage4_file.exists():
        with open(stage4_file, "r", encoding="utf-8") as f:
            morph_map = json.load(f)

    lsj_map = {}
    if stage5_file.exists():
        with open(stage5_file, "r", encoding="utf-8") as f:
            lsj_map = json.load(f)

    concordance = {}
    if stage6_file.exists():
        with open(stage6_file, "r", encoding="utf-8") as f:
            concordance = json.load(f)

    print(f"[Stage 7] Emitting sharded public dataset for {work_id}...")

    # Build letter buckets
    morph_shards = defaultdict(dict)
    for word, data in morph_map.items():
        bucket = get_greek_bucket(word)
        morph_shards[bucket][word] = data

    dict_shards = defaultdict(dict)
    for key, data in lsj_map.items():
        bucket = get_greek_bucket(key)
        dict_shards[bucket][key] = data

    lemmata_shards = defaultdict(dict)
    lemmata_index = {}
    for lemma_norm, data in concordance.items():
        bucket = get_greek_bucket(lemma_norm)
        occs = data.get("occurrences", [])
        entry = {
            "lemma": data.get("lemma", lemma_norm),
            "count": len(occs),
            "occurrences": occs[:100]  # Cap at 100 per lemma for fast loading
        }
        lemmata_shards[bucket][lemma_norm] = entry
        lemmata_index[lemma_norm] = {
            "lemma": data.get("lemma", lemma_norm),
            "count": len(occs),
            "bucket": bucket
        }

    targets = [
        REPO_ROOT / "app" / "public" / "data",
        REPO_ROOT / "static" / "data"
    ]

    for target in targets:
        work_dir = target / work_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # Write full work file
        with open(target / f"{work_id}.json", "w", encoding="utf-8") as f:
            json.dump(work_data, f, ensure_ascii=False, indent=2)

        # Write per-book files
        for book in work_data.get("books", []):
            b_num = book.get("book", 1)
            b_file = work_dir / f"book-{b_num}.json"
            with open(b_file, "w", encoding="utf-8") as f:
                json.dump(book, f, ensure_ascii=False, indent=2)

        # Write sharded morph map (merging across works)
        morph_dir = target / "morph"
        morph_dir.mkdir(parents=True, exist_ok=True)
        for bucket, shard_data in morph_shards.items():
            save_merged_json(morph_dir / f"{bucket}.json", shard_data)

        # Write sharded dictionary (merging across works)
        dict_dir = target / "dictionary"
        dict_dir.mkdir(parents=True, exist_ok=True)
        for bucket, shard_data in dict_shards.items():
            save_merged_json(dict_dir / f"{bucket}.json", shard_data)

        # Write sharded lemmata (merging across works)
        lemmata_dir = target / "lemmata"
        lemmata_dir.mkdir(parents=True, exist_ok=True)
        for bucket, shard_data in lemmata_shards.items():
            save_merged_json(lemmata_dir / f"{bucket}.json", shard_data)

        # Write top-level summary files (merging across works)
        save_merged_json(target / "morph_map.json", morph_map)
        save_merged_json(target / "dictionary.json", lsj_map)
        save_merged_json(lemmata_dir / "_index.json", lemmata_index)

    print(f"  [Stage 7] {work_id}: Emitted sharded JSON dataset ({len(morph_shards)} letter buckets) to app/public/data and static/data.")
    return work_data

