# SovereignAI source notes

Reviewed on 29–30 October 2026. These sources support the starting context and technical constraints. The proposed architecture and milestone targets in [DESIGN_PLAN.md](DESIGN_PLAN.md) remain design decisions and research hypotheses.

## User-provided shared material

[Shared ChatGPT material](https://chatgpt.com/s/t_6ae34f1877d88191bae13fa673571f57) exposed one assistant response titled “How to Invent Your Own AI Memory, Reasoning, Learning, and Intelligence Architecture.” The shared response proposed an Adaptive Cognitive Graph Engine and a controlled learning prototype. Its final architectural-choice section cuts off. The earlier user messages were not included in the retrieved message slice.

The subsequent instructions in this chat establish the actual scope: Unicode 18.0, Silicate primitives, English before mathematics, human foundational instruction, no user-supplied training corpus, Yes/No/Think better assessment, and continuing development of language and reasoning across subjects. The user later explicitly approved open dictionaries as foundation data; version 0.2 incorporates this change.

## Inspected local Silicate material

- [SilicateScratch core documentation](/Users/prdwy/Downloads/LMStudioBionic/SilicateScratch/docs/silicate-core.md): describes Object, Relation, and Derivation, identity, and record verification.
- [SilicateScratch Object implementation](/Users/prdwy/Downloads/LMStudioBionic/SilicateScratch/crates/silicate-core/src/object.rs:15): typed identity, definition/schema references, byte payload, canonical encoding.
- [SilicateScratch Relation implementation](/Users/prdwy/Downloads/LMStudioBionic/SilicateScratch/crates/silicate-core/src/relation.rs:15): directed relation, optional ordering, context.
- [SilicateScratch Derivation implementation](/Users/prdwy/Downloads/LMStudioBionic/SilicateScratch/crates/silicate-core/src/derivation.rs:35): typed inputs/outputs, execution class, operation/rule/version, parameters.
- [SilicateScratch composition documentation](/Users/prdwy/Downloads/LMStudioBionic/SilicateScratch/docs/silicate-compose.md): describes rules/schemas as stored data and composition provenance.
- [SilicateScratch Unicode documentation](/Users/prdwy/Downloads/LMStudioBionic/SilicateScratch/docs/silicate-unicode.md): describes a historical CSV/import approach; it does not establish full Unicode 18.0 coverage.
- [RustSilicate README](/Users/prdwy/Downloads/LMStudioBionic/RustSilicate/README.md): describes a smaller implementation and ordered composition/reconstruction.
- [RustSilicate record verification](/Users/prdwy/Downloads/LMStudioBionic/RustSilicate/crates/silicate-core/src/verify.rs): recomputes record identities; this is not a proof of domain truth.
- [RustSilicate storage traits](/Users/prdwy/Downloads/LMStudioBionic/RustSilicate/crates/silicate-core/src/store.rs): illustrates separation between core records and storage.

This was a targeted read, not a complete code audit or test run. The inspected variants use different Object/Relation/Derivation layouts. The plan therefore requires a pinned format, compatibility tests, and a dependency/license review before importing code. Neither source repository was modified.

## Unicode infrastructure

- [Unicode 18.0 release announcement](https://blog.unicode.org/2026/09/announcing-unicode-standard-version-180.html): official release announcement dated 16 September 2026.
- [Unicode 18.0 UCD ReadMe](https://www.unicode.org/Public/18.0.0/ucd/ReadMe.txt): identifies the versioned files as final 18.0.0 data.
- [Unicode 18.0 component page](https://www.unicode.org/versions/Unicode18.0.0/): component links. The retrieved page still included a preliminary-draft banner; the release announcement and final-data ReadMe resolve the release status.
- [UAX #44 Unicode Character Database](https://www.unicode.org/reports/tr44/): property definitions and UCD organization; pin the 18.0 revision and data during implementation.
- [UAX #15, revision 58](https://www.unicode.org/reports/tr15/tr15-58.html): Unicode 18.0 normalization reference.
- [UAX #29, revision 49](https://www.unicode.org/reports/tr29/tr29-49.html): Unicode 18.0 text segmentation reference.

The local system Python reported version 3.9.6 and `unicodedata.unidata_version == '13.0.0'`. This observation motivates explicit version pinning; it does not constrain the eventual project runtime.

On 29 October 2026, the official versioned [UCD.zip](https://www.unicode.org/Public/18.0.0/ucd/UCD.zip) and [Unihan.zip](https://www.unicode.org/Public/18.0.0/ucd/Unihan.zip) were downloaded into the project and extracted. Both ZIP CRC checks passed; the UCD ReadMe and Unihan headers identify version 18.0.0. All extracted bytes were compared with archive members. Locally calculated SHA-256 values, source URLs, sizes, and member paths are recorded in the [manifest](../data/unicode/18.0.0/manifest.json). These checksums are reproducibility records, not a comparison against separately published upstream signatures. The [local folder guide](../data/unicode/18.0.0/README.md) explains the contents. No Unicode records have yet been imported into a learner or graph database.

## Storage documentation

- [Neo4j Docker deployment](https://neo4j.com/docs/operations-manual/current/docker/introduction/): official local deployment and persistence guidance. Pin an implementation version after compatibility checks.
- [Neo4j Python transactions](https://neo4j.com/docs/python-manual/current/transactions/): managed transactions and callback retry behavior, relevant to avoiding repeated external actions or learning side effects.
- [Spanner Graph overview](https://docs.cloud.google.com/spanner/docs/graph/overview): graph/tabular interoperability, GQL-compatible interface, GoogleSQL and edition requirements.
- [Spanner Graph schema overview](https://docs.cloud.google.com/spanner/docs/graph/schema-overview): mapping underlying tables to nodes and edges.
- [Spanner emulator](https://docs.cloud.google.com/spanner/docs/emulator): local development support and limitations, including in-memory state and differences from production performance.

No Neo4j or Spanner instance has been installed, provisioned, connected, or benchmarked. M1.1 subsequently created a local Object collection with a SQLite lookup index. Neo4j remains the planned graph backend, not a measured performance comparison.

## Research foundations and novelty boundary

- [Soar architecture documentation](https://soar.eecs.umich.edu/soar_manual/02_TheSoarArchitecture/): an established reference for working memory, operators, goals, and cognitive execution. A graph plus multiple memory categories is not by itself a novel architecture.
- [Jon Doyle, A Truth Maintenance System](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a): reasons for beliefs and revision when assumptions conflict. Evidence dependencies have substantial prior history.
- [DreamCoder](https://arxiv.org/abs/2006.08381): learning reusable symbolic abstractions and program-search knowledge. It is a comparison point for library/program learning, not a component to import into this no-pretrained-model design.
- [Deep Adaptive Design](https://proceedings.mlr.press/v139/foster21a.html): learning policies for adaptive experimental design. Information-based experiment selection is an existing research direction.
- [Intrinsically Motivated Goal Exploration Processes](https://www.jmlr.org/papers/v23/21-0808.html): self-generated goals and curriculum learning. Autonomous practice and curriculum selection require evaluation against established alternatives.

The proposed contribution is a particular coupling of sparse human feedback, diagnostic contrast selection, evidence-preserving rule revision, and retention-aware promotion over the Silicate representation. This source review is not an exhaustive novelty search and does not establish that the combination is new or effective.

## Lexical resource review for version 0.2

- [Open English WordNet](https://en-word.net/) and [downloads](https://en-word.net/downloads): source-defined senses, current release formats, and resource license.
- [Princeton WordNet](https://wordnet.princeton.edu/): original project's maintenance status and distinction between words and senses.
- [Kaikki English dictionary](https://kaikki.org/dictionary/English/) and [raw extracts](https://kaikki.org/dictionary/rawdata.html): processed-download deprecation, raw source selection, and snapshot metadata.
- [Wiktextract README](https://github.com/tatuylonen/wiktextract/blob/master/README.md): extractor coverage and multilingual contents of the English-language edition. Read through the connected GitHub tool.
- [Wiktionary copyright information](https://en.wiktionary.org/wiki/Wiktionary:Copyrights): source attribution/license handling and separately sourced content.
- [Oxford API FAQ](https://developer.oxforddictionaries.com/faq) and [published API terms](https://developer.oxforddictionaries.com/api-terms-and-conditions): distinguish the products and check storage/AI-use conditions before any future dependency.
- [Merriam-Webster developer page](https://www.dictionaryapi.com/): conditions of its advertised free API tier.

The resulting design is in [LEXICAL_RESOURCES.md](LEXICAL_RESOURCES.md). No commercial account was opened and no commercial content was downloaded.

## Python environment setup

- [Python 3.11.18 release](https://www.python.org/downloads/release/python-31118/): current 3.11 security release at setup, with the series' support window.
- [uv Python installation](https://docs.astral.sh/uv/guides/install-python/) and [locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/): managed interpreters and reproducible dependency synchronization.
- [Neo4j driver installation](https://neo4j.com/docs/python-manual/current/install/): Python support and official driver installation.
- PyPI's [Pydantic](https://pypi.org/project/pydantic/), [Neo4j](https://pypi.org/project/neo4j/), and [pytest](https://pypi.org/project/pytest/) records were consulted; exact dependency distributions and hashes were resolved from PyPI into `uv.lock`.

The [environment guide](ENVIRONMENT.md) documents the installed Python 3.11.18 setup, its initial stable-release selection policy, passed smoke checks, and the distinction between the runtime's Unicode 14 tables and the project's Unicode 18 source data.

## Harness² review

[Official repository](https://github.com/google-research/harness2), [package metadata](https://github.com/google-research/harness2/blob/main/pyproject.toml), [setup guide](https://github.com/google-research/harness2/blob/main/docs/SETUP.md), [experiment guide](https://github.com/google-research/harness2/blob/main/docs/EXPERIMENTS.md), and [deterministic demo entry point](https://github.com/google-research/harness2/blob/main/harness2/cli/demo.py) were read through the connected GitHub tool on 29 October 2026. The [paper](https://arxiv.org/abs/2610.14224) supplies the research framing. The resulting [assessment](HARNESS2_ASSESSMENT.md) distinguishes fixed-weight harness optimization from SovereignAI's parameter training and independent validation. No upstream code was installed or executed during this review.

## Twelve mathematical directions reviewed for version 0.3

The [second user-provided shared response](https://chatgpt.com/s/t_6ae39bbc3ef48191a3d8169ab041991d) contains all twelve directions adapted in [MATHEMATICAL_EXTENSIONS.md](MATHEMATICAL_EXTENSIONS.md). The standard page reader exposed only a shell; a public HTTPS retrieval and JSON decoding recovered the response text without executing page scripts. The accessible plain-text and presentation versions agree on the twelve-item list. This is a read of that shared response, not a claim to have accessed unshared conversation history. A [review receipt](../manifests/mathematical-extension-source-review.json) records source identity and content hashes.

The source's three recent arXiv links were checked directly: [Geometric Algebra for Neural Networks: A Survey](https://arxiv.org/abs/2610.30121), [Tensor Methods for Language Models](https://arxiv.org/abs/2608.30505), and [Toward a Functional Geometric Algebra for Natural Language Semantics](https://arxiv.org/abs/2604.25902). Their titles match the cited topics. The adaptation treats theoretical proposals and survey assessments as research context, not demonstrated project capabilities.

Additional primary research and official technical references checked for the adaptation:

- AX01: [Geometric Algebra Transformer](https://arxiv.org/abs/2305.18415).
- AX02: [Tensorizing Neural Networks](https://arxiv.org/abs/1509.06569).
- AX03: [HDC/VSA survey, part I](https://arxiv.org/abs/2111.06077).
- AX04 and AX12: [Wavelets on Graphs via Spectral Graph Theory](https://arxiv.org/abs/0912.3848).
- AX05: [Neural Operator: Learning Maps Between Function Spaces](https://arxiv.org/abs/2108.08481); the function-space meaning is kept distinct from our near-term typed-program adaptation.
- AX06: [Low-rank lottery tickets](https://arxiv.org/abs/2205.13571).
- AX07: [SympNets](https://arxiv.org/abs/2001.03750).
- AX08: [OpenFST shortest-distance documentation](https://www.openfst.org/twiki/bin/view/FST/ShortestDistanceDoc) and [Mohri's weighted-transducer algorithms](https://research.google/pubs/generic-e-removal-and-input-e-normalization-algorithms-for-weighted-transducers/).
- AX09: [Semantic Compositionality through Recursive Matrix-Vector Spaces](https://aclanthology.org/D12-1110/).
- AX10: [Kanerva's sparse distributed memory technical report](https://ntrs.nasa.gov/api/citations/19920019632/downloads/19920019632.pdf).
- AX11: [Neural Sheaf Diffusion](https://arxiv.org/abs/2202.04579).

This was a targeted review of abstracts, bibliographic records, and technical documentation. It is not an exhaustive literature review, paper replication, or dependency/source-code audit. Component placement, test design, and priorities are SovereignAI engineering proposals. No paper's benchmark gains are extrapolated to the proposed learner.

## OpenAI development assistance

On 30 October 2026, the user authorized reuse of an existing credential and explicitly limited OpenAI to development assistance. Official [quickstart](https://developers.openai.com/api/docs/quickstart), [Python SDK documentation](https://developers.openai.com/api/reference/python), [Responses API reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create), and [model catalog](https://developers.openai.com/api/docs/models) were consulted. The [development guide](DEVELOPMENT_ASSISTANCE.md) records the implemented helper and [safe verification receipt](../manifests/development-api-verification.json). A bounded request succeeded. This authorizes developer tooling, not external teaching or grading of the learner.

## Approved M0.1 and M1.1 build evidence

The local source comparison selected Scratch V1/SHA256 at revision `71ed16a936354e828a92d5c20e11328835e77375`, with source and dependency hashes in [silicate-foundation.json](../manifests/silicate-foundation.json). This read covers the relevant canonical/identity/primitive implementations and metadata, not every crate in the source workspace. The independently written checker matches fixtures produced by the actual local Rust source. License declarations were not found in the inspected core/top-level locations; upstream source vendoring/redistribution remains unresolved. See [FOUNDATION_CONTRACT.md](FOUNDATION_CONTRACT.md).

The approved Unicode build uses only the pinned local UnicodeData.txt for its repertoire, expands First/Last ranges, rejects surrogate scalars, and creates a finite registry of engineering declaration Objects. [Collection verification](../manifests/unicode-object-verification.json) covers every Object and source record. Two bounded developer API reviews informed checks; their suggestions were inspected locally, and their outputs were not used as learner data or proof of correctness. The [collection guide](../data/objects/unicode/18.0.0/README.md) describes storage and reproduction.

## M0.3 binary internal-language foundation

The user directly requested foundational implementation of [this shared response](https://chatgpt.com/s/t_6ae44d42ba6481918fec6b463eb8ccf5). One public assistant response was available. Its six architecture stages appear in visual markup that was JSON-decoded as data, without executing source scripts. [Source hashes and coverage](../manifests/binary-language-source-review.json) distinguish the architecture reference from learner data. Illustrative English labels were not imported.

The implementation uses a bounded repeated-pattern search and a prefix-coding baseline, informed by [Huffman's original paper](https://compression.ru/download/articles/huff/huffman_1952_minimum-redundancy-codes.pdf) and [Grünwald's MDL tutorial](https://homepages.cwi.nl/~pdg/ftp/mdlintro.pdf). These references do not establish general intelligence or justify calling frequent patterns grounded semantic concepts. [The implemented contract](BINARY_FOUNDATION.md) documents actual algorithms, costs, scope, limits and measured results. The neural/RL/communication approaches mentioned in the shared response remain future research options.

One bounded M0.3 OpenAI development review used 7,075 tokens. Suggestions were checked locally; code already bounded pattern widths and total inputs, rejected empty/prefix-conflicting codes and preserved canonical scope identity. Documentation explicitly describes partial work proxies, the representation package boundary, materialized candidate counts and first-delivery retention for duplicate roots. The [verification receipt](../manifests/m0-3-verification.json) records independent checks rather than treating API claims as authority.
