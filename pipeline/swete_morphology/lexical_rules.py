"""Lexical rules, tables, deponent normalizations, and Universal Dependencies mappers."""

from __future__ import annotations

import re
import unicodedata

# Universal Dependencies UPOS -> App POS Enum Mapping
# NOUN: 4, VERB: 11, ADJECTIVE: 0, ADVERB: 2, PRONOUN_DEM: 7, PRONOUN_INTER: 8,
# PRONOUN_PRS: 9, PRONOUN_RELA: 10, CONJUNCTION: 1, INTERJECTION: 3, PREPOSITION: 5,
# ARTICLE: 6, PARTICLE: 12, PROPER_NOUN: 13, NUMBER: 14, UNSPECIFIED: 15, PRONOUN: 16
UPOS_TO_APP_POS = {
    "NOUN": 4,
    "PROPN": 13,
    "VERB": 11,
    "AUX": 11,
    "ADJ": 0,
    "ADV": 2,
    "PRON": 16,
    "DET": 6,       # Stanza tags ὁ/ἡ/τό as DET
    "ADP": 5,
    "CCONJ": 1,
    "SCONJ": 1,
    "PART": 12,
    "NUM": 14,
    "INTJ": 3,
    "PUNCT": 15,
    "X": 15,
}

DEPONENT_FIXES = {
    "πορεύω": "πορεύομαι",
    "εἰσπορεύω": "εἰσπορεύομαι",
    "ἐκπορεύω": "ἐκπορεύομαι",
    "διαπορεύω": "διαπορεύομαι",
    "παραπορεύω": "παραπορεύομαι",
    "συμπορεύω": "συμπορεύομαι",
    "ἀποκρίνω": "ἀποκρίνομαι",
    "λογίζω": "λογίζομαι",
    "βούλω": "βούλομαι",
    "δύναω": "δύναμαι",
    "ἔρχω": "ἔρχομαι",
    "δέχομαι": "δέχομαι",
    "ἀσπάζω": "ἀσπάζομαι",
    "ἀφικνέω": "ἀφικνέομαι",
    "θεάω": "θεάομαι",
    "κτάω": "κτάομαι",
    "χαρίζω": "χαρίζομαι",
    "αὐλίζω": "αὐλίζομαι",
    "ψεύδω": "ψεύδομαι",
    "ἐντέλλω": "ἐντέλλομαι",
    "φοβέω": "φοβέομαι",
    "φείδω": "φείδομαι",
    "γίνομαι": "γίνομαι",
    "γίγνομαι": "γίνομαι",
}

COMMON_LEMMA_OVERRIDES = {
    "και": "καί", "καὶ": "καί", "καί": "καί",
    "δε": "δέ", "δὲ": "δέ", "δέ": "δέ",
    "τε": "τέ", "τὲ": "τέ", "τέ": "τέ",
    "ει": "εἰ", "εἰ": "εἰ", "εἴ": "εἰ",
    "εν": "ἐν", "ἐν": "ἐν",
    "εισ": "εἰς", "εἰς": "εἰς",
    "εκ": "ἐκ", "ἐκ": "ἐκ", "εξ": "ἐκ", "ἐξ": "ἐκ",
    "προσ": "πρός", "πρὸς": "πρός", "πρός": "πρός",
    "απο": "ἀπό", "ἀπὸ": "ἀπό", "ἀπό": "ἀπό",
    "υπο": "ὑπό", "ὑπὸ": "ὑπό", "ὑπό": "ὑπό",
    "δια": "διά", "διὰ": "διά", "διά": "διά",
    "μετα": "μετά", "μετὰ": "μετά", "μετά": "μετά",
    "κατα": "κατά", "κατὰ": "κατά", "κατά": "κατά",
    "επι": "ἐπί", "ἐπὶ": "ἐπί", "ἐπί": "ἐπί",
    "περι": "περί", "περὶ": "περί", "περί": "περί",
    "συν": "σύν", "σὺν": "σύν", "σύν": "σύν",
    "ου": "οὐ", "οὐ": "οὐ", "ουκ": "οὐ", "οὐκ": "οὐ", "ουχ": "οὐ", "οὐχ": "οὐ",
    "μη": "μή", "μὴ": "μή", "μή": "μή",
    "ωσ": "ὡς", "ὡς": "ὡς", "ὥς": "ὡς",
    "ωστε": "ὥστε", "ὥστε": "ὥστε",
    "οτι": "ὅτι", "ὅτι": "ὅτι",
    "ινα": "ἵνα", "ἵνα": "ἵνα",
    "εαν": "ἐάν", "ἐάν": "ἐάν",
    "αλλα": "ἀλλά", "ἀλλὰ": "ἀλλά", "ἀλλά": "ἀλλά",
    "αλλ": "ἀλλά", "ἀλλ᾿": "ἀλλά", "ἀλλ'": "ἀλλά",
}

DECLINABLE_PROPER_NOUNS = {
    "Ἰορδάνης", "Ἰουδαία", "Ἰουδαῖος", "Ἀσσύριος", "Ἠσαΐας", "Ἠλίας",
    "Ἰησοῦς", "Μωυσῆς", "Σαμάρεια", "Ἰδουμαία", "Ἑβραῖος", "Ἀμορραῖος",
    "Αἴγυπτος", "Βαβυλών", "Φιλιστιαῖος", "Ἱεροσόλυμα", "Σιών", "Ἀντιόχεια"
}

PROPER_NOUN_CANONICAL = {
    "Ιορδάνης": "Ἰορδάνης",
    "Ιουδαία": "Ἰουδαία",
    "Ιουδαῖος": "Ἰουδαῖος",
    "Ἀσσυριος": "Ἀσσύριος",
    "Ησαιας": "Ἠσαΐας",
    "Ηλιας": "Ἠλίας",
    "Ιησους": "Ἰησοῦς",
    "Μωυσης": "Μωυσῆς",
    "Μωϋσῆς": "Μωυσῆς",
    "Σαμαρεία": "Σαμάρεια",
    "Ιερουσαλημ": "Ἰερουσαλήμ",
    "Δαυειδ": "Δαυίδ",
    "Δαυείδ": "Δαυίδ",
    "Δαυιδ": "Δαυίδ",
    "Δαυὶδ": "Δαυίδ",
    "Ισραηλ": "Ἰσραήλ",
    "Ἰσραὴλ": "Ἰσραήλ",
    "Ααρων": "Ἀαρών",
    "Ἀαρὼν": "Ἀαρών",
    "Ιακωβ": "Ἰακώβ",
    "Ἰακὼβ": "Ἰακώβ",
    "Σαουλ": "Σαούλ",
    "Σαοὺλ": "Σαούλ",
    "Σαλωμων": "Σολομών",
    "Σαλωμὼν": "Σολομών",
    "Φαραω": "Φαραώ",
    "Φαραὼ": "Φαραώ",
}


def parse_feats(feats_str: str | None) -> dict[str, str]:
    """Parse Stanza feats string (e.g. Case=Nom|Gender=Masc|Number=Sing) into a dict."""
    if not feats_str:
        return {}
    res = {}
    for part in feats_str.split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            res[k] = v
    return res


def build_morph_code(upos: str, feats: dict[str, str]) -> str:
    """Builds a classical abbreviated morphology code (e.g. V-AAI-3S, N-NSM)."""
    if upos in ("VERB", "AUX"):
        tense_map = {"Pres": "P", "Past": "A" if feats.get("Aspect") == "Perf" else "I", "Fut": "F", "Pqp": "Y"}
        voice_map = {"Act": "A", "Mid": "M", "Pass": "P"}
        mood_map = {"Ind": "I", "Sub": "S", "Opt": "O", "Imp": "M", "Inf": "N", "Part": "P"}

        t = tense_map.get(feats.get("Tense", ""), "X")
        v = voice_map.get(feats.get("Voice", ""), "A")
        m = mood_map.get(feats.get("Mood", ""), "I" if feats.get("VerbForm") == "Fin" else "X")
        p = feats.get("Person", "")
        n = "S" if feats.get("Number") == "Sing" else "P" if feats.get("Number") == "Plur" else ""
        return f"V-{t}{v}{m}-{p}{n}".rstrip("-")

    elif upos in ("NOUN", "PROPN", "ADJ", "DET", "PRON"):
        prefix = "N" if upos == "NOUN" else "N-PR" if upos == "PROPN" else "A" if upos == "ADJ" else "D" if upos == "DET" else "R"
        case = (feats.get("Case", "")[:1] or "X").upper()
        num = "S" if feats.get("Number") == "Sing" else "P" if feats.get("Number") == "Plur" else "X"
        gen = "M" if feats.get("Gender") == "Masc" else "F" if feats.get("Gender") == "Fem" else "N" if feats.get("Gender") == "Neut" else "X"
        return f"{prefix}-{case}{num}{gen}"

    elif upos == "ADP":
        return "PREP"
    elif upos in ("CCONJ", "SCONJ"):
        return "CONJ"
    elif upos == "ADV":
        return "ADV"
    elif upos == "PART":
        return "PRT"
    elif upos == "NUM":
        return "NUM"
    elif upos == "INTJ":
        return "INJ"
    return "X"
