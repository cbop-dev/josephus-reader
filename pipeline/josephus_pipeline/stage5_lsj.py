"""Stage 5: LSJ Dictionary Entry Resolution with BetaCode to Unicode Greek conversion & short gloss extraction."""

from __future__ import annotations

import json
import glob
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
import betacode.conv as betacode
from .config import Manifest, BUILD_DIR, REPO_ROOT


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", text).lower().replace("ς", "σ")


def parse_lsj_entry(body_str: str) -> tuple[str, str]:
    """Parse LSJ entry TEI XML snippet, converting BetaCode Greek to Unicode and extracting short glosses."""
    xml_str = '<entryFree>' + body_str + '</entryFree>'
    xml_str = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', xml_str)

    try:
        root = ET.fromstring(xml_str)
    except Exception:
        # Fallback if XML parsing fails
        clean = re.sub(r'<[^>]+>', ' ', body_str)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:3000], ""

    # Extract short translation glosses from <tr...> tags
    trs = [tr.text.strip() for tr in root.findall('.//tr') if tr.text and tr.text.strip()]
    seen = set()
    unique_glosses = [x for x in trs if not (x in seen or seen.add(x))]
    short_gloss = ', '.join(unique_glosses[:4])

    # Convert Greek BetaCode elements to Polytonic Unicode Greek
    def convert_greek_nodes(elem, in_greek=False):
        is_greek = in_greek or elem.attrib.get('lang') == 'greek' or elem.attrib.get('TEIform') in (
            'orth', 'foreign', 'quote', 'ref', 'itype', 'gen', 'pron'
        )
        if is_greek and elem.text:
            try:
                elem.text = betacode.beta_to_uni(elem.text)
            except Exception:
                pass
        for child in elem:
            convert_greek_nodes(child, in_greek=is_greek)
            if is_greek and child.tail:
                try:
                    child.tail = betacode.beta_to_uni(child.tail)
                except Exception:
                    pass

    convert_greek_nodes(root)

    # Flatten XML text
    def get_clean_text(elem):
        text = elem.text or ''
        for child in elem:
            text += get_clean_text(child)
            if child.tail:
                text += child.tail
        return text

    clean_def = get_clean_text(root)
    clean_def = re.sub(r'\s+', ' ', clean_def).strip()
    if len(clean_def) > 3500:
        clean_def = clean_def[:3500] + "..."

    return clean_def, short_gloss


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
                try:
                    greek_key = betacode.beta_to_uni(raw_key)
                except Exception:
                    greek_key = raw_key
                norm_key = strip_accents(greek_key)

                if norm_key in lemmata_set and norm_key not in dict_map:
                    clean_def, short_gloss = parse_lsj_entry(body)
                    dict_map[norm_key] = {
                        "key": raw_key,
                        "lemma": greek_key,
                        "gloss": short_gloss,
                        "def": clean_def
                    }

    out_dir = BUILD_DIR / "stage5" / work_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "lsj_map.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dict_map, f, ensure_ascii=False, indent=2)

    print(f"  [Stage 5] {work_id}: {len(dict_map):,} LSJ dictionary entries resolved.")
    return dict_map

