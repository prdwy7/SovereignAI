# SovereignAI

SovereignAI is a research system built on Silicate's **Object, Relation, and Derivation** primitives, with native binary observations and scoped internal pattern representations. Unicode 18.0 is its first symbolic input collection, and English remains the first human-language learning goal. The planned learner develops vocabulary, grammar, reasoning, communication and drafting through human seeds, approved dictionary foundations, generated practice and **Yes / No / Think better** feedback. Mathematics follows the English readiness gate. Imported knowledge retains its source and is evaluated separately from demonstrated understanding.

The project currently contains a design plan, verified Unicode 18.0.0 source data, a Python 3.11.18 environment, a checked three-primitive format contract, and **310,341 first-level Unicode Objects** with six declaration Objects in a local collection. **M0.2 adds a working active-object prototype:** independent atomic/group histories, explicit observation-transfer policies, transactional state transitions and replay. English learning and the planned graph/neural engines remain later builds. Subjective experience is not established by the prototype.

**M0.3 adds the binary internal-language foundation:** scoped pattern candidates, observed associations, versioned local prefix codes, raw fallback, exact reconstruction and held-out next-bit evaluation. Native bit input works independently of Unicode; a read-only adapter connects M0.2 histories. This is a bounded pattern-learning baseline, not semantic mastery.

**M1.2 adds the Unicode scalar tokenizer and ordered sequence Objects:** exact UTF-8 input, stable scalar references, ordered Relations, byte spans, replay, reconstruction and bounded local persistence. This is deterministic scalar tokenization, not a trained Unigram vocabulary. The API authored the implementation and tests under the user's instruction; Codex inspected and verified them. The full suite has **170 passing tests**, including 67 new M1.2 checks.

The user has also adopted [M0.3's numeric/tensor scaling design](docs/BINARY_FOUNDATION.md#accepted-scaling-design-numeric-values-tensors-and-bulk-storage): exact counts, explicit numeric formats, stable logical tensor identities, versioned chunk descriptors and external streamed storage. These are foundations for later roadmap-aligned builds; the scaling implementation remains pending.

OpenAI development assistance is configured through a bounded helper using the user's existing credential source. It supports developers while preserving the from-scratch learner. New builds require the user's approval of a roadmap-linked proposal before implementation.

- [Complete design and implementation plan](docs/DESIGN_PLAN.md)
- [Build approval workflow and approved slices](docs/BUILD_WORKFLOW.md)
- [Build ledger](docs/BUILD_LEDGER.md)
- [M1.2 implementation: tokenizer, ordered sequences and exact reconstruction](docs/UNICODE_SEQUENCES.md)
- [Saved M1.2 sequence artifacts and inspection commands](data/objects/sequences/m1-2/README.md)
- [M1.2 approved scope and completion record](docs/M1_2_PROPOSAL.md)
- [Pinned three-primitive foundation contract](docs/FOUNDATION_CONTRACT.md)
- [First-level Unicode Objects: storage, inspection and verification](data/objects/unicode/18.0.0/README.md)
- [Active objects: scoped histories, group connections and explicit transfer](docs/ACTIVE_OBJECTS.md)
- [Binary internal-language foundation: six stages, contracts and measured limits](docs/BINARY_FOUNDATION.md)
- [Saved native-bit and M0.2-adapter demonstrations](data/experiments/binary-language/m0-3/README.md)
- [Saved active-object demonstration](data/experiments/active-objects/m0-2/README.md)
- [OpenAI development assistance](docs/DEVELOPMENT_ASSISTANCE.md)
- [Twelve mathematical directions adapted to the architecture](docs/MATHEMATICAL_EXTENSIONS.md)
- [Inactive mathematical experiment register](experiments/mathematical_extensions.toml)
- [Architecture diagrams: selected layers and pending implementation](docs/ARCHITECTURE_STATUS.md)
- [Harness² assessment and proposed place in the improvement loop](docs/HARNESS2_ASSESSMENT.md)
- [Python environment, activation, and reproducible setup](docs/ENVIRONMENT.md)
- [T5 versus BART: selected architecture and experiment boundaries](docs/MODEL_CHOICE.md)
- [Initial data and learning contracts](docs/CONTRACTS.md)
- [Open dictionary foundation and import design](docs/LEXICAL_RESOURCES.md)
- [Downloaded Unicode 18.0.0 data and verification record](data/unicode/18.0.0/README.md)
- [Requirements, decisions, and open questions](docs/DECISIONS.md)
- [Sources and inspected local foundations](docs/SOURCES.md)

The plan distinguishes user requirements, proposed engineering decisions, research hypotheses, and acceptance targets. Future revisions should update the decision log and affected milestone criteria together.

To use the existing environment from this folder:

```sh
source .venv/bin/activate
python --version
```

To recreate or synchronize the locked environment, run `bash scripts/setup_env.sh`. Dependency changes should update `pyproject.toml` and `uv.lock` together.

## License

Copyright (C) 2020 Pridhvi Patagarla

SovereignAI is free software released under the [GNU General Public License, version 3](LICENSE). See the [LICENSE](LICENSE) file for the full license text, and <https://www.gnu.org/licenses/gpl-3.0.html> for further information.
