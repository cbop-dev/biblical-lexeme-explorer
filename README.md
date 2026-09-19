# Biblical Lexeme Explorer: Biblical Vocabulary Web Tool 2.0

An interactive, high-performance static web application for exploring and analyzing vocabulary across the Septuagint (LXX), Hebrew Bible (BHS), and Greek New Testament (SBLGNT), complete with offline LSJ dictionary lookup, frequency analysis, concordance searches, and customizable word clouds.

---

## Data Provenance & Licensing

All data assets in this repository are derived from unencumbered, openly licensed datasets and public domain resources. For the LXX, this project uses the new [OpenScriptorium/lxx-morph](https://github.com/OpenScriptorium/lxx-morph) dataset rather than the commonly used  CCAT/CATSS-derived morphological data (which is under a strict license). Thus, this project, unlike many others, can be freely shared, modified, and published under open-source licenses.

### Provenance Architecture & Flow

```mermaid
graph TD
    subgraph Upstream_Sources ["Upstream Sources & Licenses"]
        OS_MORPH["OpenScriptorium/lxx-morph<br/><b>CC BY 4.0</b><br/>• Alfred Rahlfs (1935) Septuaginta (Public Domain)<br/>• AmbroseCavalier/morpheus (CC BY-SA 3.0 US / ISC)<br/>• 59 books, 30,603 verses, 623k tokens"]
        
        OS_RESOURCES["Open Scriptures Septuagint Project<br/><b>CC BY 4.0</b><br/>• GreekWordList.js (16,368 headwords)<br/>• NT Strong's concordance numbers<br/>• gwl2AsLookups.js"]
        
        AS_LEX["Abbott-Smith Lexicon (1922)<br/><b>Public Domain</b> (TEI XML)<br/>• Manual Greek Lexicon of the New Testament<br/>• Concise English definitions"]
        
        LSJ_DICT["Perseus LSJ / Middle Liddell<br/><b>Public Domain</b><br/>• Classical & Hellenistic Greek definitions<br/>• Headword lookups"]
    end

    subgraph ETL_Pipeline ["Rebuild Pipeline (scripts/rebuild_lxx_from_openscriptorium.py)"]
        direction TB
        PARSE_OS["1. Parse OpenScriptorium JSON Seeds<br/><i>Extract tokens, surface, lemma, POS, parsing</i>"]
        NORM_GREEK["2. Unicode Diacritics Normalization<br/><i>NFC normalization, oxia (\u1F71) → tonos (\u03AC)</i>"]
        MAP_POS["3. Part-of-Speech Enum Mapping<br/><i>Map string tags ('noun', 'verb') → Numeric POSEnum</i>"]
        MAP_LEX["4. Lexicon & Gloss Enrichment<br/><i>Join lemmas with Open Scriptures, Abbott-Smith & LSJ</i>"]
        BUILD_INDEX["5. Graph & Node Indexing<br/><i>Generate sequential node IDs (books, chapters, verses, words)</i>"]
        
        PARSE_OS --> NORM_GREEK
        NORM_GREEK --> MAP_POS
        MAP_POS --> MAP_LEX
        MAP_LEX --> BUILD_INDEX
    end

    subgraph Generated_Artifacts ["Generated Static Datasets (CC BY-SA 4.0 / CC BY 4.0)"]
        LEXEMES["static/data/lxx/lexemes.json<br/><i>14,115 lemmas with gloss, pos, strongs, beta</i>"]
        SECTIONS["static/data/lxx/sections.json<br/><i>Chapter & book lexical distributions</i>"]
        CONCORDANCE["static/data/lxx/concordance.json<br/><i>Corpus-wide occurrence inverted index</i>"]
        BOOKS["static/data/lxx/books.json<br/><i>Book metadata, chapter nodes & word counts</i>"]
        VERSES["static/data/lxx/verses.json<br/><i>30,603 verse texts indexed by node ID</i>"]
        BOOK_CHAPTERS["static/data/lxx/books/*.json<br/><i>Per-book chapter/verse text hierarchies</i>"]
        CLIENT_SEARCH["src/lib/lxx/lxxLexes6.json<br/><i>Optimized client-side search index</i>"]
    end

    OS_MORPH --> PARSE_OS
    OS_RESOURCES --> MAP_LEX
    AS_LEX --> MAP_LEX
    LSJ_DICT --> MAP_LEX

    BUILD_INDEX --> LEXEMES
    BUILD_INDEX --> SECTIONS
    BUILD_INDEX --> CONCORDANCE
    BUILD_INDEX --> BOOKS
    BUILD_INDEX --> VERSES
    BUILD_INDEX --> BOOK_CHAPTERS
    BUILD_INDEX --> CLIENT_SEARCH
```

---

## Attributions & Upstream Credits

- **LXX Text & Morphology**:
  - [OpenScriptorium/lxx-morph](https://github.com/OpenScriptorium/lxx-morph) (Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
  - Base text: Alfred Rahlfs, *Septuaginta* (1935), Public Domain.
  - Morphological engine: Modernization of Perseus Morpheus ([AmbroseCavalier/morpheus](https://github.com/AmbroseCavalier/morpheus)), CC BY-SA 3.0 US / ISC.
- **English Glosses & Concordance References**:
  - [Open Scriptures Septuagint Project](https://github.com/openscriptures/GreekResources) (Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
  - G. Abbott-Smith, *A Manual Greek Lexicon of the New Testament* (1922), Public Domain (TEI XML by [translatable-exegetical-tools/Abbott-Smith](https://github.com/translatable-exegetical-tools/Abbott-Smith)).
- **Greek Lexicon / Dictionary**:
  - Liddell, Scott, Jones (LSJ) *A Greek-English Lexicon* & *Middle Liddell*, Public Domain (via Perseus Tufts & Logeion CEX).
- **Hebrew Bible (BHS)**:
  - ETCBC / Text-Fabric BHS morphological dataset.
- **Greek New Testament (SBLGNT)**:
  - SBL Greek New Testament & MorphGNT (CC BY 4.0).

---

## Licensing Terms

This project utilizes a dual-licensing structure to clearly separate application software from data assets:

- **Application Software**: Licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE). Covers all source code, SvelteKit components, engines, build scripts, and test suites.
- **Data Assets & Transformations**: Licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](LICENSE-DATA). Covers all generated JSON datasets, lexeme indexes, dictionaries, and concordance mappings.

For complete details on license scope, third-party code, and upstream data provenance, see [LICENSES.md](LICENSES.md).

---

## Rebuilding the Dataset

To re-extract and rebuild the static dataset files from source seeds:

```bash
python3 scripts/rebuild_lxx_from_openscriptorium.py
```

This updates all JSON files under `static/data/lxx/` and updates the search index at `src/lib/lxx/lxxLexes6.json`.

---

## Development & Testing

```bash
# Install dependencies
npm install

# Run unit & integration tests
npm test

# Run development server
npm run dev

# Build production bundle
npm run build

# Preview production build locally
npm run preview
```
