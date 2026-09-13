"""Stage 4: Morphological Analysis and Lemma Mapping."""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
import ast
from pathlib import Path
from .config import Manifest, BUILD_DIR, REPO_ROOT

CLTK_URL = "https://raw.githubusercontent.com/cltk/grc_models_cltk/master/lemmata/greek_lemmata_cltk.py"


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", text).lower().replace("ς", "σ")


def load_cltk_lemmatizer() -> dict:
    cache_path = REPO_ROOT / "sources" / "greek_lemmata_cltk.py"
    if not cache_path.exists():
        print("Fetching CLTK Ancient Greek Lemmatizer dictionary...")
        req = urllib.request.Request(CLTK_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        with open(cache_path, "r", encoding="utf-8") as f:
            content = f.read()

    m = re.search(r"LEMMATA\s*=\s*(\{.*\})", content, re.DOTALL)
    if m:
        return ast.literal_eval(m.group(1))
    return {}


def derive_parse_tag(word: str) -> tuple[str, str]:
    norm = strip_accents(word)
    if norm.endswith("ται"):
        return ("Pres Ind MP 3s", "Present indicative middle/passive 3rd singular")
    elif norm.endswith("νται"):
        return ("Pres Ind MP 3p", "Present indicative middle/passive 3rd plural")
    elif norm.endswith("οντο") or norm.endswith("ετο"):
        return ("Impf Ind MP 3s/p", "Imperfect indicative middle/passive 3rd person")
    elif norm.endswith("ουσιν") or norm.endswith("ουσι"):
        return ("Pres Ind Act 3p", "Present indicative active 3rd plural")
    elif norm.endswith("ει"):
        return ("Pres Ind Act 3s", "Present indicative active 3rd singular")
    elif norm.endswith("ους") or norm.endswith("ων"):
        return ("Gen Pl", "Genitive plural")
    elif norm.endswith("οις") or norm.endswith("αις") or norm.endswith("σιν"):
        return ("Dat Pl", "Dative plural")
    elif norm.endswith("ιν") or norm.endswith("ον") or norm.endswith("αν"):
        return ("Acc Sg", "Accusative singular")
    elif norm.endswith("ος"):
        return ("Nom Sg M", "Nominative singular masculine")
    elif norm.endswith("α") or norm.endswith("η"):
        return ("Nom Sg F", "Nominative singular feminine")
    return ("Form", "Greek word form")


def run_stage4(manifest: Manifest) -> dict:
    work_id = manifest.work_id
    stage3_file = BUILD_DIR / "stage3" / work_id / "tokens.json"
    if not stage3_file.exists():
        raise FileNotFoundError(f"Stage 3 output missing for {work_id}")

    with open(stage3_file, "r", encoding="utf-8") as f:
        token_data = json.load(f)

    tokens = token_data.get("tokens", [])
    print(f"[Stage 4] Performing morphological analysis for {work_id} ({len(tokens):,} unique words)...")

    cltk_dict = load_cltk_lemmatizer()
    norm_cltk = {strip_accents(k): v for k, v in cltk_dict.items()}

    morph_map = {}
    for word in tokens:
        norm = strip_accents(word)
        lemma = cltk_dict.get(word) or norm_cltk.get(norm) or word
        parse_tag, parse_desc = derive_parse_tag(word)
        entry = {
            "lemma": lemma,
            "lemma_norm": strip_accents(lemma),
            "parse": parse_tag,
            "desc": parse_desc
        }
        morph_map[word] = entry
        if norm and norm not in morph_map:
            morph_map[norm] = entry

    out_dir = BUILD_DIR / "stage4" / work_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "morph_map.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(morph_map, f, ensure_ascii=False, indent=2)

    print(f"  [Stage 4] {work_id}: {len(morph_map):,} morphological entries analyzed.")
    return morph_map
