# Unicode 18.0.0 source data

Official Unicode Character Database (UCD) and Unihan source archives, downloaded on **29 October 2026** for SovereignAI. The original archives are retained alongside all **79 extracted files**. These are the contents of the two archives below; this folder is not a mirror of every Unicode publication or separately distributed data package.

| Resource | Official source | Archive bytes | Extracted files | Extracted bytes |
|---|---|---:|---:|---:|
| [UCD archive](archives/UCD.zip) | [Unicode UCD.zip](https://www.unicode.org/Public/18.0.0/ucd/UCD.zip) | 5,657,953 | 71 | 39,580,113 |
| [Unihan archive](archives/Unihan.zip) | [Unicode Unihan.zip](https://www.unicode.org/Public/18.0.0/ucd/Unihan.zip) | 8,340,649 | 8 | 40,323,267 |

The extracted data totals **79,903,380 bytes** (about 76.2 MiB). Retained archives add **13,998,602 bytes** (about 13.4 MiB). Metadata and this guide add a small amount beyond those totals.

## Directory contents

```text
18.0.0/
  archives/
    UCD.zip
    Unihan.zip
  ucd/                    Complete extracted UCD archive
  unihan/                 Complete extracted Unihan archive
  ReadMe.upstream.txt     Upstream ReadMe copied from UCD.zip
  LICENSE.upstream.txt    Unicode License V3
  manifest.json          URLs, sizes, hashes, archive-member mapping
  SHA256SUMS             Checksums for source archives and data
  README.md              This project guide
```

Useful starting files:

- [UnicodeData.txt](ucd/UnicodeData.txt): core character records and properties.
- [DerivedAge.txt](ucd/DerivedAge.txt): version in which characters were assigned.
- [NormalizationTest.txt](ucd/NormalizationTest.txt): normalization conformance cases.
- [GraphemeBreakTest.txt](ucd/auxiliary/GraphemeBreakTest.txt): grapheme boundary cases.
- [WordBreakTest.txt](ucd/auxiliary/WordBreakTest.txt): standard word boundary cases; these do not supply English word meanings.
- [SentenceBreakTest.txt](ucd/auxiliary/SentenceBreakTest.txt): standard sentence boundary cases.
- [Upstream ReadMe](ReadMe.upstream.txt): identifies the final 18.0.0 dataset and links to its documentation.

## Verification and provenance

Both archives were retrieved over HTTPS from versioned unicode.org URLs. Every ZIP member passed its CRC check. The UCD ReadMe and each Unihan text-file header identify version 18.0.0. Extraction rejected unsafe paths and symbolic links; extracted bytes were compared with their original archive members.

[manifest.json](manifest.json) records the source URLs, byte lengths, SHA-256 values, and archive membership. [SHA256SUMS](SHA256SUMS) contains 83 checksum entries: the two archives, 79 extracted files, upstream ReadMe copy, and upstream license. The manifest, checksum list, and this guide are project-generated metadata and are not included in that checksum list.

The SHA-256 values were computed locally after download. They support later integrity checks and reproducibility; they were not compared with a separately published upstream checksum or signature. From this directory, macOS can recheck them with:

```sh
shasum -a 256 -c SHA256SUMS
```

Preserve [LICENSE.upstream.txt](LICENSE.upstream.txt) and the copyright notices when reusing the data. Its source is the [Unicode license page](https://www.unicode.org/license.txt).

## SovereignAI integration boundary

This folder supplies reference data. The subsequently approved M0.1/M1.1 builds pinned the Silicate encoding and created the [first-level Unicode Object collection](../../objects/unicode/18.0.0/README.md), including a finite declaration registry and local lookup index. Sequence tokenization, normalization/segmentation conformance, graph integration and English learning remain implementation work in [the design plan](../../../docs/DESIGN_PLAN.md).

`UnicodeData.txt` includes `First`/`Last` range records. The importer must interpret those ranges; counting lines is not a valid count of represented characters. Likewise, a Unicode scalar value, an assigned character, a rendered glyph, and a grapheme cluster are distinct concepts.

Keep Unicode names, numeric properties, case mappings, and Unihan lexical information in the infrastructure/source layer. Their presence on disk must not silently become English or mathematics knowledge in the learner. Any semantic exposure must follow the project's explicit foundation and curriculum rules.
