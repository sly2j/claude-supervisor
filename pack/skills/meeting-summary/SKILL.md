---
name: meeting-summary
description: Turn a meeting transcript, recording summary, or rough notes into concise topic-oriented minutes in plain Markdown (Meeting Summary / Open Actions / Meeting Notes) with RAID items inline per topic, suitable for email and Obsidian. Use when the user asks to summarize a meeting, write minutes or meeting notes, or extract action items, decisions, and risks from a transcript or call notes. Not for email threads (email-extraction) or reference documents (document-extraction).
argument-hint: <transcript path> [context notes]
context: fork
---

# Meeting summary

Produce portable minutes from a transcript or notes. Work in two passes: extract, then write.

Input: `$ARGUMENTS` - a transcript or notes path (or pasted text), optionally followed by context
notes on what the user considers important. Read the whole source before writing.

## Pass 0: vocabulary

If `context/vocabulary.md` exists in the project, read it and use only the sections relevant to
this meeting (people, acronyms, project names) to correct transcription errors in names and terms.
Also use any vocabulary or context the user supplies. Never invent a correction the vocabulary does
not support; mark doubtful names instead.

## Pass 1: extract

Build an internal extraction (not shown to the user). When dispatched by a lead, return this Pass 1
extraction with timestamps instead of minutes:

- **Attendees**: only people reasonably supported by the source; mark uncertainty.
- **Chronology**: meeting-level sequence only when the order changes the meaning.
- **Topic groups**: ordered subject shifts, each with its notes, decisions, actions, risks, issues.
- **Notes**: per topic, outcome bullets that each carry substance.
- **Actions**: owner, task, timing/status, source topic.
- **RAID items**: Risk, Action, Issue, Assumption, Dependency, Decision. Each item goes in exactly
  one category (pick the best fit when ambiguous) and is linked to its source topic.
- **Ambiguities**: unclear names, owners, dates, decisions, conflicting statements.

Extraction rules:

- Preserve topic order when recoverable.
- Prefer explicit decisions and outcomes over the discussion that led to them.
- Merge repeated points. Compress topics that produced no outcome to one line, or drop them if they
  carried no decision, action, risk, or noteworthy insight.
- Capture every concrete follow-up.
- If statements conflict, keep both sides and note the conflict. Record ambiguity; do not guess.

## Pass 2: write the minutes

Compress toward bottom lines, decisions, actions, and next steps. Weight topics the user's
context notes flag as important.

### Format

Plain Markdown that renders in email and in Obsidian. Bullets only, no narrative paragraphs. Never
emit an empty section or empty RAID category.

Sections, in this order:

1. `## Meeting Summary`
   - `**When:**` date/time (or `unknown`), `**Attendees:**` names (mark uncertain ones, e.g.
     `Alex (?)`).
   - An agenda only when there are 3 or more topics. Each entry is
     `- **Topic Name**: 1-2 sentence bottom line`. No label-only entries, no checkboxes.
2. `## Open Actions` - only when at least 3 follow-up actions are open. Group by owner: a bold
   owner bullet with indented checkbox sub-items (`- [ ] task (due date if stated)`). Actions with
   no stated status are open. Use `TBD` when no owner is clear.
3. `## Meeting Notes` - one `### Topic` subheading per discussion area. Within each topic:
   - 1-3 discussion bullets first.
   - Then inline RAID as bold-label bullets with indented items, omitting empty categories. Group
     actions by owner with bold owner labels (`TBD` when unclear).

### Skeleton

```markdown
## Meeting Summary

**When:** 2026-10-14, 10:00-11:00
**Attendees:** Dana, Lee, Sam (?)

- **Detector upgrade**: Vendor slipped two weeks; the team will re-plan integration around the new date.
- **Budget**: FY27 request is frozen at the current number.
- **Hiring**: Postdoc offer goes out this week.

## Open Actions

- **Dana**
  - [ ] Send revised integration plan (Fri)
- **Lee**
  - [ ] Confirm vendor delivery date in writing
  - [ ] Draft postdoc offer letter
- **TBD**
  - [ ] Book the test-beam slot

## Meeting Notes

### Detector upgrade

- Vendor delivery moved two weeks; integration tests now overlap the shutdown.
- **Risks**
  - Test-beam slot may be lost if delivery slips again
- **Decisions**
  - Re-plan integration around the new delivery date
- **Actions**
  - **Dana**: send revised integration plan (Fri)
  - **Lee**: confirm delivery date in writing
```

(The Budget and Hiring topics follow the same pattern.)

## Edge cases

- Source too short or ambiguous for meaningful minutes: say what is missing and stop; do not pad.
- Topic boundaries unclear: use the smallest credible topic structure and note it.

**Final check:** minutes start at `## Meeting Summary`, with no preamble or meta-commentary.

If the user asked for a file, write the minutes there; otherwise return them in the reply.
