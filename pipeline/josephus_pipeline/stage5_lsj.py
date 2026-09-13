"""Stage 5: LSJ Dictionary Entry Resolution."""

from __future__ import annotations

import json
import glob
import re
import unicodedata
from pathlib import Path
from .config import Manifest, BUILD_DIR, REPO_ROOT

BETA_MAP = {
    'a': 'α', 'b': 'β', 'g': 'γ', 'd': 'δ', 'e': 'ε', 'z': 'ζ', 'h': 'η', 'q': 'θ',
    'i': 'ι', 'k': 'κ', 'l': 'λ', 'm': 'μ', 'n': 'ν', 'c': 'ξ', 'o': 'ο', 'p': 'π',
    'r': 'ρ', 's': 'σ', 't': 'τ', 'u': 'υ', 'f': 'φ', 'x': 'χ', 'y': 'ψ', 'w': 'ω',
    'v': 'ϝ'
}


def betacode_to_greek(text: str) -> str:
    text = text.lower()
    return "".join(BETA_MAP[c] for c in text if c in BETA_MAP)


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", text).lower().replace("ς", "σ")


def run_stage5(manifest: Manifest) -> dict:
    work_id = manifest.work_id
    stage4_file = BUILD_DIR / "stage4" / work_id / "morph_map.json"
    if not stage4_file.exists():
        raise FileNotFoundError(f"Stage 4 output missing for {work_id}")

    with open(stage4_file, "r", encoding="utf-8") as f:
        morph_map = json.load(f)

    print(f"[Stage 5] Resolving LSJ glosses for {work_id}...")

    # Unique lemmata from stage 4
    lemmata_set = {v["lemma_norm"] for v in morph_map.values() if v.get("lemma_norm")}

    dict_map = {}
    lsj_files = sorted(glob.glob(str(REPO_ROOT / "raw_xml" / "lsj" / "grc.lsj.perseus-eng*.xml")))

    if lsj_files:
        for xml_path in lsj_files:
            with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            entries = re.findall(r'<entryFree[^>]*key=\"([^\"]+)\"[^>]*>(.*?)</entryFree>', content, re.DOTALL)
            for key, body in entries:
                raw_key = re.sub(r'\d+$', '', key).strip()
                greek_key = betacode_to_greek(raw_key)
                norm_key = strip_accents(greek_key)

                if norm_key in lemmata_set and norm_key not in dict_map:
                    clean = re.sub(r'<[^>]+>', ' ', body)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    short_def = clean[:300] + ("..." if len(clean) > 300 else "")
                    dict_map[norm_key] = {
                        "key": raw_key,
                        "lemma": greek_key,
                        "def": short_def
                    }

    out_dir = BUILD_DIR / "stage5" / work_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "lsj_map.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dict_map, f, ensure_ascii=False, indent=2)

    print(f"  [Stage 5] {work_id}: {len(dict_map):,} LSJ dictionary entries resolved.")
    return dict_map
