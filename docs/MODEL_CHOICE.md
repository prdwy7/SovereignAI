# T5 versus BART for SovereignAI

Decision date: **29 October 2026**. Status: selected architecture direction for the first neural experiment; no neural model or training framework has been installed or implemented.

**M0.3 foundation update, 30 October:** native binary patterns and versioned local prefix codes are now implemented in [BINARY_FOUNDATION.md](BINARY_FOUNDATION.md). This does not instantiate T5 or change the random-initialization requirement. A future neural frontend must bind embeddings to stable concept identities or an explicit versioned vocabulary; changing a compression codebook must not silently change the meaning of an embedding index. Unicode/English remain supported input/output mappings rather than a requirement that all internal concepts have English labels.

## Choice and scope

Choose a **small T5-style encoder–decoder initialized with random weights** for SovereignAI's first neural language component. Preserve the existing Unicode scalar interface, Silicate records, graph storage, explicit reasoning engine, and independent assessment harness.

This follows the user's request to choose between T5 and BART while preserving the earlier requirement to start without pretrained models. Architecture reuse does not supply pretrained knowledge. The custom tokenizer and curriculum mean this will be a T5-derived SovereignAI component, not a stock T5 checkpoint with its published capabilities.

The earlier plan specifies symbolic grammar learning and rule execution. Adding a trainable neural component is an extension to that plan. The symbolic implementation remains the first baseline; evaluate whether a neural component improves it before making neural inference a required dependency.

## Why T5 is the first candidate

T5 presents diverse language tasks through a common text-to-text interface. BART is also an encoder–decoder and its original training approach reconstructs text after corruption; its paper reports both generation and comprehension results. Both can be trained on multiple tasks. The choice here is based on the fit between T5's task formulation and our curriculum, not a claim that BART cannot reason, draft, or handle structured outputs. [T5 paper](https://arxiv.org/abs/1910.10683), [BART paper](https://arxiv.org/abs/1910.13461).

| Project need | Proposed T5-derived use | Assessment |
|---|---|---|
| Progressive language acquisition | Copy symbols, complete verified word forms, fill missing spans, then construct phrases and sentences | Appropriate experimental fit; success depends on available examples and learning signal |
| Multiple English skills | Use task identifiers for definition, parsing, answering, revision, and drafting | Consistent training interface; BART could implement this too |
| Structured meaning and graph access | Encode bounded, explicitly serialized context; decode proposed text or typed expressions | Requires a custom bridge and output validator for either architecture |
| Continued learning | Train versioned candidate checkpoints from approved experience and replay | Requires the harness; neither architecture supplies safe continual improvement automatically |
| Expert reasoning and communication | Combine generated candidates with explicit reasoning, evidence, and assessment | An evaluation target, not a property established by choosing T5 |

There is no evidence yet that T5 is more sample-efficient than BART under SovereignAI's exact seed/dictionary/three-button-feedback constraints. Published pretrained results do not answer that question.

## Initialization and Unicode interface

- Initialize model and embedding weights randomly. Do not download T5, FLAN-T5, ByT5, or BART pretrained weights.
- Use SovereignAI's own symbol registry and tokenizer. Standard T5 uses a learned unigram vocabulary associated with SentencePiece; standard BART uses a learned BPE vocabulary. Loading those tokenizers would introduce externally learned segmentation. Both architectures can instead receive our custom token IDs. [T5 implementation documentation](https://huggingface.co/docs/transformers/model_doc/t5), [BART implementation documentation](https://huggingface.co/docs/transformers/model_doc/bart).
- Preserve Unicode scalar Objects as the canonical text representation. Model vocabulary indices are separate addresses into embedding tables, with a reversible mapping to source scalars. They are not Silicate hashes or evidence of meaning.
- Start neural experiments on the declared English exercise alphabet. Keep the full Unicode registry available to the symbolic layer. Until a lossless fallback or vocabulary expansion is implemented, unsupported neural input must return an explicit unsupported-input result; never silently collapse distinct symbols into one unknown token.
- Reserve control IDs separately from literal text, including task, padding, end-of-sequence, and corruption markers. Version the vocabulary, masks, and tokenization with every checkpoint.
- If vocabulary expansion is implemented, preserve old IDs, initialize only new rows, migrate optimizer state consistently, and retest retained skills. Do not renumber existing symbols.
- Retain original scalar sequences through normalization and segmentation views. Python's Unicode 14 tables remain unsuitable as the project's Unicode 18 property authority.

ByT5 is a useful comparison because it applies a T5-derived architecture to UTF-8 byte sequences. Bytes and Unicode scalar objects are different units. A future byte-based alternative would require an explicit mapping back to scalar spans and its own benchmark; it is not silently substituted for the chosen scalar interface. [ByT5 paper](https://arxiv.org/abs/2105.13626).

## Division of responsibility

1. **Silicate core:** identities, Objects, Relations, Derivations, and structural checks.
2. **Graph memory:** versioned meanings, rules, source assertions, observations, and assessments.
3. **Context builder:** retrieve a bounded subgraph and serialize only the context authorized for the task. Keep evaluator targets and hidden labels out of learner inputs.
4. **T5-derived component:** propose expressions, interpretations, or revisions. Generated text and apparent reasoning remain hypotheses until evaluated.
5. **Explicit engine and assessors:** check syntax, grounded meanings, derivations, task outcomes, and human criteria as applicable. A valid parse alone does not establish truth.
6. **Harness:** own curriculum, optimizer steps, replay sampling, budgets, evaluation, checkpoint promotion, and rollback. Neural outputs cannot directly edit accepted graph state.

Model tensors and optimizer state belong in versioned checkpoint artifacts. Reference their hashes, training-data manifest, vocabulary version, configuration, and evaluation results through Silicate Objects and Derivations. Do not store every individual weight as a graph node. Do not describe generated prose as a verified derivation.

The user-adopted [M0.3 scaling design](BINARY_FOUNDATION.md#accepted-scaling-design-numeric-values-tensors-and-bulk-storage) makes this explicit: exact integer model counts, dtype/shape/layout descriptors, logical tensor digests, separate versioned chunk/storage representations and bounded streaming. The first neural integration remains small and randomly initialized; larger parameter-count metadata alone does not establish model execution capacity. These tensor/storage contracts are accepted architecture awaiting later approved implementation.

## Learning signal and data

Training a randomly initialized transformer still requires training examples and an optimization objective. In this project, those examples come from approved dictionaries, human seeds, independently checked exercises, and appropriately scoped assessment records. These constitute a recorded training dataset even though the user does not supply a corpus.

Begin with supervised target prediction on tasks with available correct targets and denoising on approved source text. Add graph-conditioned tasks only when their interfaces and independent validators exist. A dictionary definition can provide source text; reconstructing it is not evidence that its meaning is grounded or that the learner can use it correctly.

Human feedback applies only to the displayed criterion and exact output version. Yes is not blanket validation of every claim in a response. No does not reveal a unique corrected answer. Think better requests another attempt and has no automatic numerical truth label. Any later feedback-driven optimization needs an explicitly specified objective and held-out evaluation; none of these responses is itself an optimizer.

Self-generated text without independent validation must not be promoted to authoritative training targets merely because the generator agrees with it. Broad English expertise from the proposed information budget remains an unproven research goal.

## First experiment and promotion gate

After the M1 symbol interface and initial M2 seed/assessment loop are operational:

1. Profile available memory and compute and select a small model configuration, batch size, and sequence limit. Do not infer feasibility from a published model's name or parameter count.
2. Freeze source exposure and train/validation/test splits by source and compositional task family before constructing exercises.
3. Measure the symbolic baseline, the T5-derived component, and their combination. If comparing with BART, match tokenization, permitted data, tuning effort, and resource budgets, and report parameter counts and actual compute separately.
4. Evaluate semantic correctness, grammar, unseen compositions, drafting criteria, calibration/abstention, retention, latency, memory, and human-assessment cost. Report variation across repeated runs where feasible.
5. Promote a checkpoint only when it improves the declared tasks without exceeding retention and resource limits. Keep the prior checkpoint and its tokenizer available for rollback.

This decision selects the first architecture to investigate. It does not establish a delivered neural capability or an expert-language milestone. Dependency installation, precise model dimensions, loss weighting, and feedback optimization remain implementation decisions after profiling and interface design.

## Version 0.3 mathematical experiments

The twelve-direction adaptation retains this T5-style choice and its initial dense baseline. [MATHEMATICAL_EXTENSIONS.md](MATHEMATICAL_EXTENSIONS.md) assigns tensor-network components to AX02 and dynamic low-rank capacity to AX06. Evaluate each only after the baseline runs; record shape/rank, tensorization, optimizer-state migration, actual memory/latency, task quality and retention. A lower parameter count is not itself a completed efficiency improvement.

AX03/AX04/AX10/AX11/AX12 can contribute independently evaluated retrieval or diagnostic artifacts to the context bridge. They do not supply pretrained embeddings or automatically change the tokenizer. AX05/AX08/AX09 strengthen the explicit transformation/search path; AX01/AX07 are grounded-domain branches. Freeze accepted memory/harness versions during neural comparisons and retain canonical source references throughout. The [experiment register](../experiments/mathematical_extensions.toml) leaves all additions inactive.
