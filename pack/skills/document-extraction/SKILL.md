---
name: document-extraction
description: Extract structured substance from a reference document (paper, report, proposal, spec, white paper, slide deck text) - metadata, section structure, key claims, evidence, methods, implications, limitations, open questions - as a neutral intermediate artifact. Use when a document must be digested before someone else writes from it (summary, literature notes, a proposal section, a brief), or when asked to "pull out the key findings/claims" of a document. Not for meeting transcripts (meeting-summary) or email threads (email-extraction).
---

# Document extraction

Extract the recall-worthy substance of a reference document into a compact artifact that a
downstream writer (usually the `writer` lead or a `writer-worker`) maps into its own format.

## Scope

- Extract content only. Do not choose templates, presentation style, file destinations, or final
  prose. Do not edit files or insert notes.
- Meeting transcripts: use `meeting-summary`. Email threads: use `email-extraction`.

## Rules

- Input is the raw document plus optional vocabulary or domain context.
- Preserve the source section structure when clear; otherwise group by topic shifts.
- Distinguish claims, evidence, methods, implications, and limitations.
- Extract specific findings ("X reduces Y by 30% on dataset Z"), not labels ("the paper discusses
  X").
- Include methodology only when it affects how a claim should be read.
- Include implications and open questions only when stated or strongly supported; label inferred
  items.
- Include RAID items (risk, action, issue, assumption, dependency, decision) only when the document
  explicitly contains them, each in exactly one category.
- Record ambiguity instead of guessing. Omit boilerplate.

## Fields

- **Document metadata**: authors, date, type, source/publication, version when available.
- **Section groups**: ordered source sections or topic groups.
- **Key claims/findings**: 1-4 substantive bullets per section.
- **Evidence/methodology**: data, support, assumptions, or methods needed to judge a claim.
- **Implications**: stated or strongly implied relevance, next steps, broader significance.
- **Limitations**: caveats, constraints, scope boundaries, author-stated assumptions.
- **Open questions**: unresolved questions, gaps, future work.
- **RAID items**: only when explicitly present.
- **Citations**: only key cited works material to the claims.
- **Ambiguities**: unclear provenance, unsupported assertions, conflicts, fragile interpretations.

## Edge cases

- Too sparse or unclear: say what is missing.
- Unclear authorship or provenance: keep the ambiguity visible.
- Sections that conflict: extract both positions and note the conflict.
- No discernible structure: use the smallest credible topic grouping and say so.

## Output

A compact two-layer artifact, factual and free of presentation markup:

- **Document level**: metadata, overall significance, cross-cutting themes, global ambiguities.
- **Per section group** (in order): label, key claims/findings, evidence/methodology,
  implications, limitations, open questions, RAID (only when warranted), local ambiguities.

Before returning, check that every item traces to the document or is labeled inferred/uncertain,
and that section notes are substantive rather than exhaustive.
