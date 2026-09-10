# AI / ML pipeline

```
Data ingestion (synthetic seed / POST /api/analyze/text)
   |
Data cleaning (regex normalization inside the NLP extractor)
   |
Entity extraction (app/ai/nlp_extraction.py)
   |
Entity resolution (app/ai/entity_resolution.py -- surfaces candidates, never merges)
   |
Relationship extraction (extract_relationships_hint, from the same text pass)
   |
Graph construction (app/graph/graph_builder.py, from the relationships table)
   |
Graph analytics (app/analytics/centrality.py, community.py)
   |
Anomaly detection (app/analytics/anomaly_detection.py, 10 explainable rules)
   |
Risk indicators / finding labels (shared four-label vocabulary, everywhere)
   |
Investigator visualization (Cytoscape.js graph, dashboards, reports)
```

## Why offline, rule-based components instead of a hosted LLM/spaCy model

The brief requires the prototype to run **without any paid API**, and to keep working
with **no internet connection** once dependencies are installed. Two consequences:

1. **No external LLM call anywhere.** The "AI investigation assistant"
   (`app/ai/ai_assistant.py`) answers by pattern-matching the question (case id,
   entity id, "why flagged", "strongest connections", "multiple cases", "timeline"
   keywords) and querying the local database directly. This is a real, deliberate
   constraint, not a corner cut: because it never calls a model, it **cannot
   hallucinate a fact that isn't in the dataset** -- every answer either cites the
   exact ids that support it, or returns the literal string *"No supporting
   information was found in the available dataset."*

2. **No spaCy model download.** spaCy's statistical NER pipelines are hundreds of
   megabytes and need to be fetched separately from the `spacy` package itself; a
   prototype that must "start locally without requiring paid APIs" and work offline
   can't assume that download has happened. `app/ai/nlp_extraction.py` instead
   implements the "lightweight NLP alternative" the brief explicitly allows: a small
   set of regex patterns plus a gazetteer, each tagged with the exact rule that
   produced it, so a match is always explainable by construction ("this is a PHONE
   because it matched the 10-digit pattern," not "the model said so").

Both choices trade some raw recall/precision (a real transformer NER model would
catch more edge cases) for **full explainability, zero external dependency, and zero
hallucination risk** -- which matter more for an investigative decision-support tool
than they do for a general-purpose chatbot.

## Entity extraction

`extract_entities(text)` runs a fixed, ordered list of patterns
(`app/ai/nlp_extraction.py:PATTERNS`) over the input text: EMAIL, PHONE, VEHICLE
(Indian-style plate), ACCOUNT, CASE id, DATE, ORGANIZATION (name + Ltd/Pvt/Bank/...
suffix), then PERSON (a "Person X" or capitalized-name-pair heuristic), plus a
separate LOCATION gazetteer pass and a FINANCIAL_ENTITY amount-cue pass.

**Span tracking prevents overlap.** ORGANIZATION is matched *before* PERSON, and
every match claims its character span; a later, looser pattern (PERSON's
capitalized-word-pair heuristic) is not allowed to re-claim a span an earlier, more
specific pattern already matched. Without this, "Coastal Traders Pvt Ltd" would be
extracted correctly as one ORGANIZATION *and* incorrectly split into two bogus PERSON
matches ("Coastal Traders", "Pvt Ltd") by the generic capitalized-word-pair rule --
this was an actual bug caught and fixed during development
(`tests/test_extraction.py::test_organization_not_split_into_spurious_persons` is a
regression test for it).

Every extracted entity carries a **confidence score set by which pattern matched it**
(`_confidence_for`): structural patterns with almost no false-positive surface
(email, phone, plate, account, case id, date) get 0.95; ORGANIZATION 0.8; PERSON
0.65-0.7 (free-text name heuristics can false-positive on any capitalized two-word
phrase); FINANCIAL_ENTITY 0.75. This is a fixed, inspectable lookup table, not a
learned score.

## Relationship extraction

`extract_relationships_hint` splits the text into sentences, and where two
PERSON/ORGANIZATION entities co-occur with a relationship verb cue ("met", "called",
"transferred", "travelled", "communicated"), proposes a candidate relationship typed
to the matching verb (or `ASSOCIATED_WITH` as the fallback). Every candidate is
labeled `"Potential connection"` and carries the exact sentence it came from as
evidence -- **`POST /api/analyze/text` never writes these to the database**; they are
returned to the investigator as leads only.

## Entity resolution

`app/ai/entity_resolution.find_possible_duplicate_persons` compares every pair of
`Person` records using Python's standard-library `difflib.SequenceMatcher` for name
similarity, plus a check for shared direct graph connections (same phone, same
organization, etc. -- anything linked to both candidates). Each result reports its
`confidence`, the specific `possible_matching_attributes` that drove it, and
`"recommendation": "Requires investigator verification before merging or linking
these records."` **Nothing is ever auto-merged**; there is no code path anywhere in
the app that combines two entity records.

## Graph construction & analytics

See `docs/ARCHITECTURE.md` for why the graph is built on demand from the relational
`relationships` table rather than stored separately. Once built:

- **Centrality** (`compute_centrality`): degree, betweenness, closeness, and PageRank
  via `networkx`, computed on a simplified (parallel-edges-collapsed) copy of the
  multigraph, since standard centrality algorithms assume simple graphs.
- **Community detection** (`detect_communities`): `networkx`'s greedy-modularity
  algorithm, deterministic for a given graph.
- **Bridge entities** (`identify_bridge_entities`): an entity whose immediate
  neighbors span more than one detected community.

## The shared finding-label vocabulary and why the score formula was fixed mid-build

`explain_entity_score` is the single function every "how connected/risky is this
entity" surface calls (entity detail, case AI insights, network analysis, PDF/JSON
reports). It combines degree centrality, betweenness centrality, and a
**graph-size-normalized** PageRank into a 0-100 score, then maps that score to one of
the four required labels (`Analytical lead` >= 75, `Risk indicator` >= 45, otherwise
`Potential connection`), plus a plain-language reason list built from the same
numbers (connection count, related-case count, whether it's a detected bridge, high
betweenness).

Two real bugs were found and fixed while building this, both worth documenting
because they're the kind of subtle error this domain can't afford:

1. **PageRank needs graph-size normalization.** PageRank values sum to 1 across all
   nodes in a graph, so an "average" node's raw PageRank shrinks as the graph grows
   (~1/N). The first version of the score formula multiplied raw PageRank by a fixed
   constant tuned for a small graph, which meant that on any larger graph almost
   every entity's score saturated at the 100 cap. The fix normalizes PageRank by
   `graph_size` before weighting it, so an "average" node lands near a fixed point on
   the 0-100 scale regardless of how big the graph is.
2. **Never score an entity against its own 1-hop neighborhood.** The entity-detail
   endpoint originally built a graph via a 1-hop BFS *centered on the entity being
   scored* and ran centrality on that. In a star graph, the center node is trivially
   the most connected/central node by construction (degree centrality = 1.0,
   betweenness = 1.0) -- so *every* entity in the dataset would score as maximally
   central just because it's always the center of its own neighborhood view. The fix
   scores an entity within the real case graph(s) it belongs to instead.
   `tests/test_entities.py::test_entity_scores_are_differentiated` is a regression
   test asserting scores aren't degenerate across a sample of entity types.

## Suspicious-pattern detection (10 explainable rules)

`app/analytics/anomaly_detection.py` implements all ten patterns from the brief as
independent, individually testable functions (`rule_unusual_communication_frequency`,
`rule_sudden_communication_increase`, `rule_repeated_interactions`,
`rule_financial_anomaly`, `rule_shared_vehicle_across_cases`,
`rule_shared_phone_multiple_entities`, `rule_repeated_location_movement`,
`rule_entities_shared_across_cases`, `rule_rapid_connectivity_change`,
`rule_unusual_time_window_activity`). Every rule returns a draft alert with a
severity computed from a fixed threshold table (`_pct_bucket`), a `detection_rule`
string identifying exactly which rule fired, a plain-language `evidence` string
citing the specific numbers observed, and a `label` from the four-label vocabulary --
never a bare "suspicious" flag with no explanation. `run_all_rules` aggregates them;
`tests/test_alerts.py::test_anomaly_detection_rules_cover_all_ten_patterns` asserts
every single rule can actually fire against the seeded dataset (the seed generator
deliberately plants a handful of qualifying patterns -- e.g. a genuine circular fund
flow, a phone shared by three persons, a burst of very recent low-baseline
communication -- specifically so this isn't a detector with a silent gap that never
triggers in the demo).

## What this pipeline will not do

It will not, at any stage, output a bare risk number with no explanation, merge
entities automatically, assert a relationship as fact rather than a lead, or answer a
question with information not present in the local dataset. Every one of those
constraints has a corresponding test in `backend/tests/`.
