# Open dictionary foundations for SovereignAI

Version 0.2 — 29 October 2026 — Approved knowledge-source scope; importers not implemented

The user has approved open dictionaries as explicit foundation data. This changes the earlier seed-only design. SovereignAI still uses its own representational and learning machinery, without a pretrained language model. The user need not assemble a training dataset, but the system will consume external lexical datasets. Experiments must identify that knowledge accurately.

## Source choices and verified corrections

**Open English WordNet is the proposed first source.** It exposes lexical senses and relations in structured form. The official downloads page currently lists the 2025 base release and a 2025+ release that additionally includes curated proper names. Start with the base release and pin a specific archive, hash, and format. WN-LMF XML is a suitable first interchange format; retain its source identifiers and relation endpoints. The project publishes the resource under CC BY 4.0. [Official downloads](https://en-word.net/downloads).

Princeton confirms that its original WordNet is no longer developed and identifies community successors. WordNet relates particular word senses, rather than treating all uses of a spelling as one meaning. Its main coverage is nouns, verbs, adjectives, and adverbs. It does not supply the complete function-word, grammar, discourse, and reasoning curriculum required here. [Princeton WordNet](https://wordnet.princeton.edu/).

**Wiktionary through Kaikki/Wiktextract is the proposed second source.** The English dictionary page marks its processed download as deprecated and directs data consumers to raw Wiktextract data. The raw English-language Wiktionary edition contains entries for many languages, so the importer must explicitly select English entries and separately handle any approved translingual material. Pin the dump date, extraction version, and file checksum; stream the JSONL rather than loading it all into memory. [Kaikki English page](https://kaikki.org/dictionary/English/), [raw downloads](https://kaikki.org/dictionary/rawdata.html).

The extractor supports glosses, grammatical information, inflected forms, pronunciations, usage qualifiers, and other lexical fields when present. Missing fields remain unknown. Imported labels and descriptions are source knowledge, not categories the learner independently discovered. [Wiktextract documentation](https://github.com/tatuylonen/wiktextract/blob/master/README.md).

**Commercial dictionaries are deferred.** Oxford's published API terms include restrictions on AI usage and local storage; ordinary API access must not be treated as permission for this system. A separately suitable agreement would be necessary before making Oxford a dependency. Its API is also distinct from the historical Oxford English Dictionary product. [Oxford API terms](https://developer.oxforddictionaries.com/api-terms-and-conditions), [Oxford FAQ](https://developer.oxforddictionaries.com/faq).

Merriam-Webster's public free API conditions specify noncommercial use, at most 1,000 queries per day per key, and at most two reference APIs. Those access conditions alone do not establish permission for persistent ingestion or every proposed AI use. Neither commercial service is required for the initial open lexical foundation. [Merriam-Webster developer page](https://www.dictionaryapi.com/).

## How the records map to Silicate

Keep these concepts separate:

| Object type | Content and purpose |
|---|---|
| WrittenForm | Exact Unicode scalar sequence; reconstructed through ordered composition |
| SourceLexicalEntry | Source-scoped lemma, part of speech, homograph/etymology distinction where available |
| SourceSense | A particular source's meaning identifier and attributes |
| SourceSynset | A WordNet grouping of senses with a shared source-defined concept |
| DefinitionText | Original gloss as text, with source and license provenance |
| SourceAssertion | Source-defined relation, form, usage property, or definition claim |
| Concept | SovereignAI's grounded or hypothesized internal concept |
| AlignmentHypothesis | A revisable proposed mapping between source senses or to an internal concept |
| ExposureRecord | Which source records a learner could retrieve at a particular stage |
| CompetenceEvidence | Independent tasks and assessments demonstrating use or interpretation |

A simplified example is one written form, `run`, connected to different source senses for movement, operating something, and managing an activity. These are illustrative labels, not asserted source IDs or an exhaustive sense inventory. Different noun and verb entries, idioms, and multiword forms must remain distinguishable.

Preserve whether a relation connects lexical senses or synsets. Do not indiscriminately convert every source relation into one generic concept edge. Relation schemas specify direction, endpoint kinds, and permitted inference. Synonymy does not authorize substitution in every sentence; a lexical hierarchy does not establish unrestricted causal or commonsense facts.

Composition Derivations record how written forms were assembled from Unicode atoms. Import Derivations record the source artifact, record locator, parser/mapping version, and produced records. Later reasoning Derivations identify the imported assertions and teacher rules used as premises. A derivation documenting import proves provenance of the transformation, not the truth or understanding of every imported statement.

## Origin, grounding, and competence

Maintain independent dimensions:

```text
knowledge_origin: teacher | imported | observed | derived | hypothesized
source_assertion_state: retained | disputed | superseded
grounding_state: ungrounded | partially_grounded | grounded_in_context
competence_state: unassessed | practicing | demonstrated_in_scope
```

These labels are proposed domain-schema values, not additional core primitives. Correct use can improve competence while the knowledge origin remains imported. A graph traversal can establish what a source says without establishing that the system can interpret or apply the meaning.

Glosses initially can remain opaque sequences. A definition referring to unknown words cannot bootstrap all its own meanings through circular lookup. Teacher-grounded primitives, declared relation semantics, operational tasks, and assessment still connect this reference graph to usable concepts.

## Import and activation pipeline

1. **Acquire a pinned artifact.** Keep the original compressed file, source URL, release/dump date, extraction version, checksum, and applicable notices.
2. **Validate and parse.** Reject malformed or oversized records, resolve the supported source schema, disable XML external entity/network resolution, and preserve extraction errors. Missing references are reported, not invented.
3. **Retain source identity.** Use source/release/entry/sense identifiers. Where stable sense IDs are absent, use a documented snapshot-local locator and original-record commitment. Do not pretend an array index is stable across releases.
4. **Build canonical Silicate records.** Exact source strings become Unicode sequences. Record field-level provenance, source relation kinds, and import Derivations. Canonical object identity is computed by the selected kernel format.
5. **Stage and index.** Batch into Neo4j through the storage contract. The reference inventory is separately queryable from active grounded concepts and mastered skills. Import retries are idempotent.
6. **Select an active subset.** Begin around teacher-seeded concepts and the current English curriculum. This is a task-relevant subset, not a frequency ranking inferred without a corpus.
7. **Teach use and test meaning.** Generate new contexts and diagnostic contrasts. Ground useful meanings through approved environments and Yes/No/Think better assessment. Log source retrieval/exposure during each attempt.
8. **Expand and reevaluate.** Activate further entries when they support a capability gap; run retention checks. Source-release upgrades produce new assertions and explicit migration records.

Importing a reference archive does not expose all of it automatically to the learner. Enforce curriculum scope in retrieval, not just in the user interface. Mathematics-specific semantic facts, external encyclopedic links, quoted examples, media, and translations are disabled by default until their scope and applicable rights are established. This preserves the English-before-mathematics progression while allowing English terminology to be introduced deliberately.

## Cross-source alignment and disagreement

Do not merge source senses on spelling alone. Match candidates using compatible part of speech, form/inflection relationships, declared source links, known concept context, and locally understood definitions. Do not introduce a pretrained embedding model to automate alignment.

An uncertain match is an AlignmentHypothesis with supporting evidence and alternatives. Sources retain their own IDs even after a mapping is accepted. A disagreement can indicate differing sense granularity, dialect, register, extraction failure, or a real conflict. Record those possibilities rather than choosing whichever source was imported last.

Source updates can split, merge, or remove senses. Preserve old source assertions, mark supersession, invalidate dependent caches, and reconsider affected internal alignments and learned rules. Do not rewrite historical assessments against new definitions.

## Attribution and export

Every source assertion retains source release, source record/page locator, attribution/license reference, extraction/import version, and modification lineage. Source links and notices accompany applicable exports and displayed definitions. A mixed-source graph does not automatically have one uniform license.

Wiktionary text carries attribution/share-alike conditions, and individual quotations or media can have separate rights. Record the conditions associated with the selected dump and fields; initially exclude third-party quotations and audio/media. The software license of an extractor is not the license of the extracted dictionary content. [Wiktionary copyright information](https://en.wiktionary.org/wiki/Wiktionary:Copyrights).

These are implementation requirements for traceable source use. Exact permission for a future distribution must be evaluated against the chosen content and applicable license text; no commercial agreement has been requested or accepted.

## Evaluation changes and acceptance tests

Preserve a teacher-only baseline for comparison, then add an Open English WordNet condition and an OEWN-plus-Wiktionary condition. Compare learners under matched source exposure, human feedback, and compute budgets. Also compare ordinary dictionary retrieval against the proposed learner so a successful lookup is not misreported as an improvement in reasoning.

Label evaluations by what they test: reference retrieval, interpretation, contextual use, new compositions, or transfer. Answers present verbatim in imported definitions/examples are not unseen generalization. Track direct and nearby source exposure, hold out new task constructions, and keep human/audit evaluation independent of the learner's own paraphrases.

Milestone M1L must demonstrate:

- Exact Unicode reconstruction, including non-ASCII and multiword entries.
- Separate identities for polysemous entries and different source senses.
- Preservation of lexical-versus-synset relation endpoints and direction.
- Field-level source attribution and a reproducible import manifest.
- Idempotent reimport and resumable batches without duplicating evidence.
- Isolation between reference inventory, active curriculum, and demonstrated competence.
- No premature mathematics/encyclopedic knowledge activation.
- Reversible cross-source mappings and correct handling of missing/changed records.
- A successful contextual-use assessment whose provenance distinguishes imported knowledge from learned behavior.

No WordNet or Wiktionary dataset has been downloaded or imported as part of this plan revision. The separately requested Unicode 18.0 download is infrastructure for the symbol layer.
