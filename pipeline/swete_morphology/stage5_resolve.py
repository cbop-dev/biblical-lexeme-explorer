"""Stage 5: Constraint Solver & Morphological Resolution Engine.

Combines:
  - Gazetteer and Proper Name Heuristics (Stage 2)
  - Stanza Neural Predictions (Stage 4)
  - Lexical Normalization Rules & Deponent Fixes

Emits:
  - pipeline/build/swete_resolved_tokens.json: Fully resolved tokens with lemma, pos, morph, confidence.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

from .config import (
    BUILD_DIR,
    GAZETTEER_FILE,
    RESOLVED_TOKENS_FILE,
    TOKENS_FILE,
)
from .lexical_rules import (
    COMMON_LEMMA_OVERRIDES,
    DEPONENT_FIXES,
    UPOS_TO_APP_POS,
)

STANZA_OUT_FILE = BUILD_DIR / "swete_stanza.json"

# Closed class words with 100% fixed POS
CLOSED_CLASS_POS = {
    "καί": 1, "δέ": 1, "τε": 1, "ἀλλά": 1, "ὅτι": 1, "ἵνα": 1, "εἰ": 1, "ἐάν": 1, "ὥστε": 1, "ὅτε": 1, "ὅταν": 1,
    "ἐν": 5, "εἰς": 5, "ἐκ": 5, "πρός": 5, "ἀπό": 5, "ὑπό": 5, "διά": 5, "μετά": 5, "κατά": 5, "ἐπί": 5, "περί": 5, "σύν": 5, "ἀνά": 5, "ὑπέρ": 5, "ἕως": 5, "πρό": 5,
    "οὐ": 12, "μή": 12, "ἄν": 12, "δή": 12, "οὖν": 12, "μέν": 12, "γε": 12, "ναί": 12, "ἆρα": 12,
    "ὁ": 6,
}


def resolve():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading tokens from Stage 1...")
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        tokens = json.load(f)

    print("Loading gazetteer from Stage 2...")
    with open(GAZETTEER_FILE, "r", encoding="utf-8") as f:
        gazetteer = json.load(f)

    print(f"Loading Stanza predictions from {STANZA_OUT_FILE}...")
    with open(STANZA_OUT_FILE, "r", encoding="utf-8") as f:
        stanza_preds = json.load(f)

    print(f"Resolving {len(tokens):,} tokens...")
    resolved = []
    stats = Counter()

    for t in tokens:
        t_id = str(t["id"])
        surface = t["surface"]
        norm = t["norm"]
        is_cap = t["is_cap"]
        is_start = t["is_sentence_start"]

        stanza_info = stanza_preds.get(t_id, {})
        s_lemma = stanza_info.get("lemma", surface.lower())
        s_pos = stanza_info.get("pos", 15)
        s_morph = stanza_info.get("morph", "X")
        s_upos = stanza_info.get("upos", "X")

        # 1. Gazetteer & Proper Name check
        # Check if capitalized (and especially non-sentence-start or in gazetteer)
        gaz_match = gazetteer.get(surface) or gazetteer.get(norm)
        if gaz_match and (not is_start or is_cap):
            lemma = gaz_match["lemma"]
            pos = 13  # PROPER_NOUN
            is_indecl = gaz_match.get("is_indecl", False)
            if is_indecl:
                morph = "N-PRI"
            else:
                morph = s_morph if s_morph.startswith("N-") else "N-PR"
            confidence = 0.98
            source = "gazetteer"
            stats["proper_name"] += 1

        # 2. Closed-class overrides (prepositions, conjunctions, particles, article)
        elif s_lemma in CLOSED_CLASS_POS:
            lemma = s_lemma
            pos = CLOSED_CLASS_POS[s_lemma]
            morph = s_morph
            confidence = 0.99
            source = "closed_class"
            stats["closed_class"] += 1

        # 3. Lexical normalizations (deponents, overrides)
        else:
            lemma = COMMON_LEMMA_OVERRIDES.get(s_lemma, s_lemma)
            lemma = DEPONENT_FIXES.get(lemma, lemma)
            pos = s_pos
            morph = s_morph
            confidence = 0.95 if s_upos != "X" else 0.70
            source = "stanza_proiel"
            stats["stanza_neural"] += 1

        resolved_token = {
            "id": t["id"],
            "book": t["book"],
            "chapter": t["chapter"],
            "verse": t["verse"],
            "ref": t["ref"],
            "surface": surface,
            "punct": t["punct"],
            "norm": norm,
            "lemma": lemma,
            "pos": pos,
            "morph": morph,
            "confidence": confidence,
            "source": source,
        }
        resolved.append(resolved_token)

    print("\nResolution Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v:,} ({v / len(tokens) * 100:.1f}%)")

    print(f"\nWriting resolved tokens to {RESOLVED_TOKENS_FILE}...")
    with open(RESOLVED_TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(resolved, f, ensure_ascii=False)

    print("Stage 5 completed successfully!")


if __name__ == "__main__":
    resolve()
