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
    DECLINABLE_PROPER_NOUNS,
    DEPONENT_FIXES,
    PROPER_NOUN_CANONICAL,
    UPOS_TO_APP_POS,
)

STANZA_OUT_FILE = BUILD_DIR / "swete_stanza.json"

# Closed class words with 100% fixed POS
CLOSED_CLASS_POS = {
    "καί": 1, "δέ": 1, "τε": 1, "ἀλλά": 1, "ὅτι": 1, "ἵνα": 1, "εἰ": 1, "ἐάν": 1, "ὥστε": 1, "ὅτε": 1, "ὅταν": 1, "ἤ": 1,
    "ἐν": 5, "εἰς": 5, "ἐκ": 5, "πρός": 5, "ἀπό": 5, "ὑπό": 5, "διά": 5, "μετά": 5, "κατά": 5, "ἐπί": 5, "περί": 5, "σύν": 5, "ἀνά": 5, "ὑπέρ": 5, "ἕως": 5, "πρό": 5,
    "οὐ": 12, "μή": 12, "ἄν": 12, "δή": 12, "οὖν": 12, "μέν": 12, "γε": 12, "ναί": 12, "ἆρα": 12,
    "ὁ": 6,
}

# Exact Greek article forms (never match relative pronouns ὃ, ὅ, ἥ, ἣ, ᾗ, οἳ, or conjunction ἢ)
ARTICLE_SURFACES = {
    "ὁ", "ἡ", "τό", "τὸ", "τόν", "τὸν", "τήν", "τὴν", "τοῦ", "του", "τῆς", "της", "τῷ", "τῳ", "τῇ", "τῃ",
    "οἱ", "αἱ", "τά", "τὰ", "τούς", "τοὺς", "τάς", "τὰς", "τῶν", "των", "τοῖς", "τοις", "ταῖς", "ταις",
    "Ὁ", "Ἡ", "Τό", "Τὸ", "Τόν", "Τὸν", "Τήν", "Τὴν", "Τοῦ", "Τῆς", "Τῷ", "Τῇ",
    "Οἱ", "Αἱ", "Τά", "Τὰ", "Τούς", "Τοὺς", "Τάς", "Τὰς", "Τῶν", "Τοῖς", "Ταῖς",
}

# Relative pronoun forms
RELATIVE_PRONOUN_SURFACES = {
    "ὅς", "ὃς", "ἥ", "ἣ", "ὅ", "ὃ", "οὗ", "ἧς", "ᾧ", "ᾗ", "ὅν", "ὃν", "ἥν", "ἣν",
    "οἵ", "οἳ", "αἵ", "αἳ", "ἅ", "ἃ", "ὧν", "οἷς", "αἷς", "οὕς", "οὓς", "ἅς", "ἃς",
    "Ὅς", "Ὃς", "Ἥ", "Ἣ", "Ὅ", "Ὃ", "Οὗ", "Ἧς", "ᾯ", "ᾟ", "Ὅν", "Ὃν", "Ἥν", "Ἣν",
    "Οἵ", "Οἳ", "Αἵ", "Αἳ", "Ἅ", "Ἃ", "Ὧν", "Οἷς", "Αἷς", "Οὕς", "Οὓς", "Ἅς", "Ἃς"
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

        # Normalize neural lemma with overrides early
        s_lemma_clean = COMMON_LEMMA_OVERRIDES.get(s_lemma, s_lemma)
        s_lemma_clean = DEPONENT_FIXES.get(s_lemma_clean, s_lemma_clean)

        if norm.startswith("πρεσβυτερ") and s_lemma_clean == "πρέσβυς":
            s_lemma_clean = "πρεσβύτερος"
            s_pos = 0

        if norm.startswith("παρεπικραν") and s_lemma_clean == "ἐπικραίνω":
            s_lemma_clean = "παραπικραίνω"

        if norm.startswith("ανεστρεψ") and s_lemma_clean == "ἀνατρέπω":
            s_lemma_clean = "ἀναστρέφω"

        if norm.startswith("παρεμβαλλ") and s_lemma_clean == "παραβάλλω":
            s_lemma_clean = "παρεμβάλλω"

        # 1. Definite Article check (exact surfaces only)
        if surface in ARTICLE_SURFACES or (s_lemma == "ὁ" and s_upos == "DET"):
            lemma = "ὁ"
            pos = 6  # ARTICLE
            morph = s_morph if (s_morph.startswith("RA") or s_morph.startswith("D-")) else "RA"
            confidence = 0.99
            source = "article_rule"
            stats["article"] += 1

        # 2. Relative Pronoun check
        elif surface in RELATIVE_PRONOUN_SURFACES or s_lemma in ("ὅς", "ὁς") or (s_upos == "PRON" and s_lemma_clean in ("ὅς", "ὁς")):
            lemma = "ὅς"
            pos = 10  # PRONOUN_RELA
            morph = s_morph if s_morph.startswith("R-") else "R-NSM"
            confidence = 0.99
            source = "relative_pronoun"
            stats["relative_pronoun"] += 1

        # 3. High-frequency special overrides (divine titles, particles, adverbs)
        elif norm in ("κυριοσ", "κυριου", "κυριω", "κυριον", "κυριε") or s_lemma_clean == "κύριος":
            lemma = "κύριος"
            pos = 4  # NOUN
            morph = s_morph if s_morph.startswith("N-") else "N-NSM"
            confidence = 0.99
            source = "kyrios_override"
            stats["kyrios"] += 1

        elif norm in ("θεοσ", "θεου", "θεω", "θεον", "θεε", "θεοι", "θεων", "θεοισ", "θεουσ") or s_lemma_clean == "θεός":
            lemma = "θεός"
            pos = 4  # NOUN
            morph = s_morph if s_morph.startswith("N-") else "N-NSM"
            confidence = 0.99
            source = "theos_override"
            stats["theos"] += 1

        elif surface in ("ἐάν", "ἐὰν", "Ἐάν", "Ἐὰν"):
            lemma = "ἐάν"
            pos = 1  # CONJUNCTION
            morph = "CONJ"
            confidence = 0.99
            source = "ean_override"
            stats["ean"] += 1

        elif surface in ("πρωί", "πρωὶ", "πρωΐ", "πρωῒ", "Πρωί", "Πρωὶ"):
            lemma = "πρωί"
            pos = 2  # ADVERB
            morph = "ADV"
            confidence = 0.99
            source = "proi_override"
            stats["proi"] += 1

        elif surface in ("ᾅδου", "ᾅδης", "ᾅδην", "ᾅδῃ", "Ἅιδης", "ἅδης") or s_lemma_clean in ("ᾅδης", "Ἅιδης"):
            lemma = "ᾅδης"
            pos = 4  # NOUN
            morph = s_morph if s_morph.startswith("N-") else "N-NSM"
            confidence = 0.99
            source = "hades_override"
            stats["hades"] += 1

        elif surface in ("ἔδεσθε", "ἔδεται", "ἔδονται", "ἔδομαι", "ἔδηται"):
            lemma = "ἐσθίω"
            pos = 11  # VERB
            morph = s_morph if s_morph.startswith("V-") else "V-FMI-3S"
            confidence = 0.99
            source = "esthio_override"
            stats["esthio"] += 1

        elif surface in ("πρόσχες", "πρόσχετε", "Πρόσχες", "Πρόσχετε"):
            lemma = "προσέχω"
            pos = 11  # VERB
            morph = s_morph if s_morph.startswith("V-") else "V-AAM-2S"
            confidence = 0.99
            source = "prosecho_override"
            stats["prosecho"] += 1

        elif surface in ("ἐλέη", "ἐλεῶν") and s_lemma_clean in ("ἐλέη", "ἔλεος", "ἐλεέω"):
            lemma = "ἔλεος"
            pos = 4  # NOUN
            morph = s_morph if s_morph.startswith("N-") else "N-APN"
            confidence = 0.99
            source = "eleos_override"
            stats["eleos"] += 1

        # 4. Closed-class overrides (prepositions, conjunctions, particles)
        elif s_lemma_clean in CLOSED_CLASS_POS:
            lemma = s_lemma_clean
            pos = CLOSED_CLASS_POS[s_lemma_clean]
            morph = s_morph
            confidence = 0.99
            source = "closed_class"
            stats["closed_class"] += 1

        # 5. Sentence-initial tokens: presume COMMON word unless confirmed proper name
        elif is_start:
            # Check if it matches a confirmed proper name in gazetteer or canonical list
            if surface in PROPER_NOUN_CANONICAL or (surface in gazetteer and s_upos == "PROPN"):
                gaz_match = gazetteer.get(surface) or {"lemma": PROPER_NOUN_CANONICAL.get(surface, surface), "is_indecl": True}
                lemma = gaz_match["lemma"]
                pos = 13  # PROPER_NOUN
                is_indecl = gaz_match.get("is_indecl", False)
                morph = "N-PRI" if is_indecl else (s_morph if s_morph.startswith("N-") else "N-PR")
                confidence = 0.98
                source = "gazetteer_sentence_start"
                stats["proper_name"] += 1
            # If Stanza predicts a common word category
            elif s_upos in ("VERB", "AUX", "DET", "ADP", "CCONJ", "SCONJ", "PART", "PRON") and s_pos != 13:
                lemma = s_lemma_clean
                pos = s_pos
                morph = s_morph
                confidence = 0.95
                source = "sentence_start_common"
                stats["sentence_start_common"] += 1
            elif (surface in gazetteer or norm in gazetteer) and (s_upos == "PROPN" or s_pos == 13 or (surface not in ARTICLE_SURFACES and s_upos not in ("VERB", "AUX"))):
                gaz_match = gazetteer.get(surface) or gazetteer.get(norm)
                lemma = gaz_match["lemma"]
                pos = 13  # PROPER_NOUN
                is_indecl = gaz_match.get("is_indecl", False)
                morph = "N-PRI" if is_indecl else (s_morph if s_morph.startswith("N-") else "N-PR")
                confidence = 0.98
                source = "gazetteer_sentence_start"
                stats["proper_name"] += 1
            else:
                lemma = s_lemma_clean
                pos = s_pos
                morph = s_morph
                confidence = 0.90
                source = "stanza_neural"
                stats["stanza_neural"] += 1

        # 6. Non-sentence-initial tokens: capitalization indicates proper name
        elif is_cap:
            gaz_match = gazetteer.get(surface) or gazetteer.get(norm)
            if gaz_match:
                lemma = gaz_match["lemma"]
                pos = 13  # PROPER_NOUN
                is_indecl = gaz_match.get("is_indecl", False)
                morph = "N-PRI" if is_indecl else (s_morph if s_morph.startswith("N-") else "N-PR")
                confidence = 0.98
                source = "gazetteer_mid_sentence"
                stats["proper_name"] += 1
            elif s_upos == "PROPN" or s_pos == 13:
                propn_lemma = PROPER_NOUN_CANONICAL.get(surface) or PROPER_NOUN_CANONICAL.get(s_lemma_clean) or s_lemma_clean
                lemma = propn_lemma if propn_lemma else surface
                pos = 13
                morph = s_morph if s_morph.startswith("N-") else "N-PR"
                confidence = 0.90
                source = "stanza_proper_name"
                stats["proper_name"] += 1
            else:
                lemma = s_lemma_clean
                pos = s_pos
                morph = s_morph
                confidence = 0.92
                source = "stanza_neural"
                stats["stanza_neural"] += 1

        # 7. Default: general neural tagging
        else:
            lemma = s_lemma_clean
            pos = s_pos
            morph = s_morph
            confidence = 0.95 if s_upos != "X" else 0.70
            source = "stanza_neural"
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
