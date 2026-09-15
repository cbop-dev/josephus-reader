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


# Closed-class paradigm dictionary: word_norm -> (pos, parse_tag, parse_desc)
KNOWN_PARADIGMS: dict[str, tuple[str, str, str]] = {
    # Article: ὁ, ἡ, τό
    "ο": ("article", "Nom Sg M", "Nominative singular masculine"),
    "η": ("article", "Nom Sg F", "Nominative singular feminine"),
    "το": ("article", "Nom/Acc Sg N", "Nominative/accusative singular neuter"),
    "του": ("article", "Gen Sg M/N", "Genitive singular masculine/neuter"),
    "τησ": ("article", "Gen Sg F", "Genitive singular feminine"),
    "τω": ("article", "Dat Sg M/N", "Dative singular masculine/neuter"),
    "τη": ("article", "Dat Sg F", "Dative singular feminine"),
    "τον": ("article", "Acc Sg M", "Accusative singular masculine"),
    "την": ("article", "Acc Sg F", "Accusative singular feminine"),
    "οι": ("article", "Nom Pl M", "Nominative plural masculine"),
    "αι": ("article", "Nom Pl F", "Nominative plural feminine"),
    "τα": ("article", "Nom/Acc Pl N", "Nominative/accusative plural neuter"),
    "των": ("article", "Gen Pl M/F/N", "Genitive plural masculine/feminine/neuter"),
    "τοισ": ("article", "Dat Pl M/N", "Dative plural masculine/neuter"),
    "ταισ": ("article", "Dat Pl F", "Dative plural feminine"),
    "τουσ": ("article", "Acc Pl M", "Accusative plural masculine"),
    "τασ": ("article", "Acc Pl F", "Accusative plural feminine"),

    # Demonstrative: οὗτος, αὕτη, τοῦτο
    "ουτοσ": ("pronoun", "Nom Sg M", "Nominative singular masculine"),
    "αυτη": ("pronoun", "Nom Sg F", "Nominative singular feminine"),
    "τουτο": ("pronoun", "Nom/Acc Sg N", "Nominative/accusative singular neuter"),
    "τουτου": ("pronoun", "Gen Sg M/N", "Genitive singular masculine/neuter"),
    "ταυτησ": ("pronoun", "Gen Sg F", "Genitive singular feminine"),
    "τουτω": ("pronoun", "Dat Sg M/N", "Dative singular masculine/neuter"),
    "ταυτη": ("pronoun", "Dat Sg F", "Dative singular feminine"),
    "τουτον": ("pronoun", "Acc Sg M", "Accusative singular masculine"),
    "ταυτην": ("pronoun", "Acc Sg F", "Accusative singular feminine"),
    "ουτοι": ("pronoun", "Nom Pl M", "Nominative plural masculine"),
    "αυται": ("pronoun", "Nom Pl F", "Nominative plural feminine"),
    "ταυτα": ("pronoun", "Nom/Acc Pl N", "Nominative/accusative plural neuter"),
    "τουτων": ("pronoun", "Gen Pl M/F/N", "Genitive plural masculine/feminine/neuter"),
    "τουτοισ": ("pronoun", "Dat Pl M/N", "Dative plural masculine/neuter"),
    "ταυταισ": ("pronoun", "Dat Pl F", "Dative plural feminine"),
    "τουτουσ": ("pronoun", "Acc Pl M", "Accusative plural masculine"),
    "ταυσ": ("pronoun", "Acc Pl F", "Accusative plural feminine"),

    # Relative & Personal Pronouns
    "οσ": ("pronoun", "Nom Sg M", "Nominative singular masculine"),
    "η": ("pronoun", "Nom Sg F", "Nominative singular feminine"),
    "ο": ("pronoun", "Nom/Acc Sg N", "Nominative/accusative singular neuter"),
    "ου": ("pronoun", "Gen Sg M/N", "Genitive singular masculine/neuter"),
    "ησ": ("pronoun", "Gen Sg F", "Genitive singular feminine"),
    "ω": ("pronoun", "Dat Sg M/N", "Dative singular masculine/neuter"),
    "ον": ("pronoun", "Acc Sg M", "Accusative singular masculine"),
    "ην": ("pronoun", "Acc Sg F", "Accusative singular feminine"),
    "οι": ("pronoun", "Nom Pl M", "Nominative plural masculine"),
    "αι": ("pronoun", "Nom Pl F", "Nominative plural feminine"),
    "α": ("pronoun", "Nom/Acc Pl N", "Nominative/accusative plural neuter"),
    "οισ": ("pronoun", "Dat Pl M/N", "Dative plural masculine/neuter"),
    "αισ": ("pronoun", "Dat Pl F", "Dative plural feminine"),
    "ουσ": ("pronoun", "Acc Pl M", "Accusative plural masculine"),
    "ασ": ("pronoun", "Acc Pl F", "Accusative plural feminine"),

    "εγω": ("pronoun", "Nom Sg", "Nominative 1st singular"),
    "εμου": ("pronoun", "Gen Sg", "Genitive 1st singular"),
    "εμοι": ("pronoun", "Dat Sg", "Dative 1st singular"),
    "εμε": ("pronoun", "Acc Sg", "Accusative 1st singular"),
    "μου": ("pronoun", "Gen Sg", "Genitive 1st singular"),
    "μοι": ("pronoun", "Dat Sg", "Dative 1st singular"),
    "με": ("pronoun", "Acc Sg", "Accusative 1st singular"),
    "ημεισ": ("pronoun", "Nom Pl", "Nominative 1st plural"),
    "ημων": ("pronoun", "Gen Pl", "Genitive 1st plural"),
    "ημιν": ("pronoun", "Dat Pl", "Dative 1st plural"),
    "ημασ": ("pronoun", "Acc Pl", "Accusative 1st plural"),

    "συ": ("pronoun", "Nom Sg", "Nominative 2nd singular"),
    "σου": ("pronoun", "Gen Sg", "Genitive 2nd singular"),
    "σοι": ("pronoun", "Dat Sg", "Dative 2nd singular"),
    "σε": ("pronoun", "Acc Sg", "Accusative 2nd singular"),
    "υμεισ": ("pronoun", "Nom Pl", "Nominative 2nd plural"),
    "υμων": ("pronoun", "Gen Pl", "Genitive 2nd plural"),
    "υμιν": ("pronoun", "Dat Pl", "Dative 2nd plural"),
    "υμασ": ("pronoun", "Acc Pl", "Accusative 2nd plural"),

    "αυτοσ": ("pronoun", "Nom Sg M", "Nominative singular masculine"),
    "αυτη": ("pronoun", "Nom Sg F", "Nominative singular feminine"),
    "αυτο": ("pronoun", "Nom/Acc Sg N", "Nominative/accusative singular neuter"),
    "αυτου": ("pronoun", "Gen Sg M/N", "Genitive singular masculine/neuter"),
    "αυτησ": ("pronoun", "Gen Sg F", "Genitive singular feminine"),
    "αυτω": ("pronoun", "Dat Sg M/N", "Dative singular masculine/neuter"),
    "αυτη": ("pronoun", "Dat Sg F", "Dative singular feminine"),
    "αυτον": ("pronoun", "Acc Sg M", "Accusative singular masculine"),
    "αυτην": ("pronoun", "Acc Sg F", "Accusative singular feminine"),
    "αυτοι": ("pronoun", "Nom Pl M", "Nominative plural masculine"),
    "αυται": ("pronoun", "Nom Pl F", "Nominative plural feminine"),
    "αυτα": ("pronoun", "Nom/Acc Pl N", "Nominative/accusative plural neuter"),
    "αυτων": ("pronoun", "Gen Pl M/F/N", "Genitive plural masculine/feminine/neuter"),
    "αυτοισ": ("pronoun", "Dat Pl M/N", "Dative plural masculine/neuter"),
    "αυταισ": ("pronoun", "Dat Pl F", "Dative plural feminine"),
    "αυτουσ": ("pronoun", "Acc Pl M", "Accusative plural masculine"),
    "αυτασ": ("pronoun", "Acc Pl F", "Accusative plural feminine"),

    "τισ": ("pronoun", "Nom Sg M/F", "Nominative singular masculine/feminine"),
    "τι": ("pronoun", "Nom/Acc Sg N", "Nominative/accusative singular neuter"),
    "τινοσ": ("pronoun", "Gen Sg", "Genitive singular"),
    "τινι": ("pronoun", "Dat Sg", "Dative singular"),
    "τινα": ("pronoun", "Acc Sg M/F / Nom/Acc Pl N", "Accusative singular / Neuter plural"),
    "τινεσ": ("pronoun", "Nom Pl M/F", "Nominative plural masculine/feminine"),
    "τινων": ("pronoun", "Gen Pl", "Genitive plural"),
    "τισι": ("pronoun", "Dat Pl", "Dative plural"),
    "τισιν": ("pronoun", "Dat Pl", "Dative plural"),
    "τινασ": ("pronoun", "Acc Pl M/F", "Accusative plural masculine/feminine"),

    # Prepositions
    "εν": ("preposition", "Prep", "Preposition (+ Dat)"),
    "εισ": ("preposition", "Prep", "Preposition (+ Acc)"),
    "εσ": ("preposition", "Prep", "Preposition (+ Acc)"),
    "εκ": ("preposition", "Prep", "Preposition (+ Gen)"),
    "εξ": ("preposition", "Prep", "Preposition (+ Gen)"),
    "προσ": ("preposition", "Prep", "Preposition (+ Gen/Dat/Acc)"),
    "μετα": ("preposition", "Prep", "Preposition (+ Gen/Acc)"),
    "κατα": ("preposition", "Prep", "Preposition (+ Gen/Acc)"),
    "δια": ("preposition", "Prep", "Preposition (+ Gen/Acc)"),
    "επι": ("preposition", "Prep", "Preposition (+ Gen/Dat/Acc)"),
    "υπο": ("preposition", "Prep", "Preposition (+ Gen/Dat/Acc)"),
    "απο": ("preposition", "Prep", "Preposition (+ Gen)"),
    "παρα": ("preposition", "Prep", "Preposition (+ Gen/Dat/Acc)"),
    "περι": ("preposition", "Prep", "Preposition (+ Gen/Dat/Acc)"),
    "συν": ("preposition", "Prep", "Preposition (+ Dat)"),
    "ξυν": ("preposition", "Prep", "Preposition (+ Dat)"),
    "υπερ": ("preposition", "Prep", "Preposition (+ Gen/Acc)"),
    "αμφι": ("preposition", "Prep", "Preposition (+ Gen/Dat/Acc)"),
    "αντι": ("preposition", "Prep", "Preposition (+ Gen)"),
    "ανα": ("preposition", "Prep", "Preposition (+ Acc)"),
    "ανευ": ("preposition", "Prep", "Preposition (+ Gen)"),
    "ενεκα": ("preposition", "Prep", "Preposition (+ Gen)"),
    "χωρισ": ("preposition", "Prep", "Preposition (+ Gen)"),

    # Conjunctions & Particles
    "και": ("conjunction", "Conj", "Conjunction / Adverb"),
    "δε": ("conjunction", "Conj", "Conjunction / Particle"),
    "τε": ("conjunction", "Conj", "Conjunction"),
    "αλλα": ("conjunction", "Conj", "Conjunction"),
    "γαρ": ("conjunction", "Conj", "Conjunction"),
    "ουν": ("conjunction", "Conj", "Conjunction"),
    "οτι": ("conjunction", "Conj", "Conjunction"),
    "ει": ("conjunction", "Conj", "Conjunction"),
    "η": ("conjunction", "Conj", "Conjunction / Particle"),
    "μη": ("conjunction", "Adv/Conj", "Negative particle / Conjunction"),
    "ου": ("conjunction", "Adv/Conj", "Negative particle"),
    "ουκ": ("conjunction", "Adv/Conj", "Negative particle"),
    "ουχ": ("conjunction", "Adv/Conj", "Negative particle"),
    "ωστε": ("conjunction", "Conj", "Conjunction"),
    "επει": ("conjunction", "Conj", "Conjunction"),
    "οτε": ("conjunction", "Conj", "Conjunction"),
    "ινα": ("conjunction", "Conj", "Conjunction"),
    "οπωσ": ("conjunction", "Conj", "Conjunction / Adverb"),
    "καιτοι": ("conjunction", "Conj", "Conjunction"),
    "μεν": ("particle", "Part", "Particle"),
    "αρα": ("particle", "Part", "Particle"),
    "γε": ("particle", "Part", "Particle"),
    "δη": ("particle", "Part", "Particle"),
    "μην": ("particle", "Part", "Particle"),
    "τοι": ("particle", "Part", "Particle"),
    "ουδε": ("conjunction", "Conj", "Conjunction / Negative particle"),
    "μηδε": ("conjunction", "Conj", "Conjunction / Negative particle"),
}


def derive_parse_tag(word: str) -> tuple[str, str, str]:
    """Derive Part of Speech, short parse tag, and detailed parse description for Ancient Greek word form."""
    norm = strip_accents(word)

    # 1. Check known closed-class paradigms (Articles, Pronouns, Prepositions, Conjunctions)
    if norm in KNOWN_PARADIGMS:
        return KNOWN_PARADIGMS[norm]

    # 2. Check suffix patterns (using medial sigma 'σ')
    if norm.endswith("ται"):
        return ("verb", "Pres Ind MP 3s", "Present indicative middle/passive 3rd singular")
    elif norm.endswith("νται"):
        return ("verb", "Pres Ind MP 3p", "Present indicative middle/passive 3rd plural")
    elif norm.endswith("οντο") or norm.endswith("ετο"):
        return ("verb", "Impf Ind MP 3s/p", "Imperfect indicative middle/passive 3rd person")
    elif norm.endswith("ουσιν") or norm.endswith("ουσι"):
        return ("verb", "Pres Ind Act 3p", "Present indicative active 3rd plural")
    elif norm.endswith("ειν") or norm.endswith("εσθαι") or norm.endswith("σθαι") or norm.endswith("ναι"):
        return ("verb", "Inf", "Infinitive")
    elif norm.endswith("ει"):
        return ("verb", "Pres Ind Act 3s", "Present indicative active 3rd singular")
    elif norm.endswith("οισ") or norm.endswith("οισιν"):
        return ("noun", "Dat Pl M/N", "Dative plural masculine/neuter")
    elif norm.endswith("αισ") or norm.endswith("αισιν"):
        return ("noun", "Dat Pl F", "Dative plural feminine")
    elif norm.endswith("ουσ"):
        return ("noun", "Acc Pl M / Gen Sg", "Accusative plural masculine / Genitive singular")
    elif norm.endswith("ων"):
        return ("noun", "Gen Pl", "Genitive plural")
    elif norm.endswith("ου"):
        return ("noun", "Gen Sg M/N", "Genitive singular masculine/neuter")
    elif norm.endswith("ω"):
        return ("noun", "Dat Sg M/N", "Dative singular masculine/neuter")
    elif norm.endswith("οσ"):
        return ("noun", "Nom Sg M", "Nominative singular masculine")
    elif norm.endswith("ησ") or norm.endswith("ασ"):
        return ("noun", "Gen/Acc Sg F", "Genitive or accusative singular feminine")
    elif norm.endswith("η") or norm.endswith("α"):
        return ("noun", "Nom Sg F / Nom Pl N", "Nominative singular feminine / Neuter plural")
    elif norm.endswith("ον") or norm.endswith("αν") or norm.endswith("ιν"):
        return ("noun", "Acc Sg / Nom Sg N", "Accusative singular / Neuter nominative singular")

    return ("", "Form", "Greek word form")


COMMON_LEMMA_OVERRIDES = {
    "και": "καί", "καὶ": "καί", "καί": "καί",
    "δε": "δέ", "δὲ": "δέ", "δέ": "δέ",
    "τε": "τέ", "τὲ": "τέ", "τέ": "τέ",
    "ει": "εἰ", "εἰ": "εἰ", "εἴ": "εἰ",
    "εν": "ἐν", "ἐν": "ἐν",
    "εισ": "εἰς", "εἰς": "εἰς", "εσ": "εἰς",
    "εκ": "ἐκ", "ἐκ": "ἐκ", "εξ": "ἐκ", "ἐξ": "ἐκ",
    "προσ": "πρός", "πρὸς": "πρός", "πρός": "πρός",
    "απο": "ἀπό", "ἀπὸ": "ἀπό", "ἀπό": "ἀπό",
    "υπο": "ὑπό", "ὑπὸ": "ὑπό", "ὑπό": "ὑπό",
    "δια": "διά", "διὰ": "διά", "διά": "διά",
    "μετα": "μετά", "μετὰ": "μετά", "μετά": "μετά",
    "κατα": "κατά", "κατὰ": "κατά", "κατά": "κατά",
    "επι": "ἐπί", "ἐπὶ": "ἐπί", "ἐπί": "ἐπί",
    "περι": "περί", "περὶ": "περί", "περί": "περί",
    "παρα": "παρά", "παρὰ": "παρά", "παρά": "παρά",
    "ο": "ὁ", "η": "ἡ", "το": "ὁ", "του": "ὁ", "τησ": "ὁ", "τω": "ὁ", "τη": "ὁ", "τον": "ὁ", "την": "ὁ",
    "οι": "ὁ", "αι": "ὁ", "τα": "ὁ", "των": "ὁ", "τοισ": "ὁ", "ταισ": "ὁ", "τουσ": "ὁ", "τασ": "ὁ"
}


def normalize_lemma_accents(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).replace("\u0300", "\u0301"))


def run_stage4(manifest: Manifest) -> dict:
    work_id = manifest.work_id
    stage3_file = BUILD_DIR / "stage3" / work_id / "tokens.json"
    if not stage3_file.exists():
        from .stage3_tokenize import run_stage3
        run_stage3(manifest)

    with open(stage3_file, "r", encoding="utf-8") as f:
        token_data = json.load(f)

    tokens = token_data.get("tokens", [])
    print(f"[Stage 4] Performing morphological analysis for {work_id} ({len(tokens):,} unique words)...")

    cltk_dict = load_cltk_lemmatizer()
    norm_cltk = {}
    for k, v in cltk_dict.items():
        norm_k = strip_accents(k)
        if norm_k not in norm_cltk or k == v:
            norm_cltk[norm_k] = v

    morph_map = {}
    for word in tokens:
        norm = strip_accents(word)
        lemma = (
            COMMON_LEMMA_OVERRIDES.get(word)
            or COMMON_LEMMA_OVERRIDES.get(norm)
            or cltk_dict.get(word)
            or norm_cltk.get(norm)
            or word
        )
        lemma = normalize_lemma_accents(lemma)
        pos, parse_tag, parse_desc = derive_parse_tag(word)
        entry = {
            "lemma": lemma,
            "lemma_norm": strip_accents(lemma),
            "pos": pos,
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
