# check_iana_consistency.py — Specification and Processing Rules

## Purpose

Programmatically verifies consistency between the normative object definitions
and the IANA registry tables in `src/draft-ietf-rpp-data-objects.md`, and can
export the full structured object model — including prose not captured by any
structured field — as YAML.

Both the consistency check and the normative object model are built from a
single shared parse (`parse_document()`); the YAML export does not re-parse
the draft independently.

## Usage

PyYAML is needed only for `--yaml-out`; `--check` alone needs nothing beyond
the stdlib. Check whether it is already available before installing anything:

```bash
python3 -c "import yaml"
```

If that fails, install into a virtualenv — never into the global/system
Python (see [.scripts/CLAUDE.md](CLAUDE.md)):

```bash
python3 -m venv .venv
.venv/bin/pip install -r .scripts/requirements.txt
```

Run from the `src/` directory, using whichever interpreter has PyYAML
available:

```bash
cd src
python3 ../.scripts/check_iana_consistency.py [OPTIONS]
```

| Flag | Effect |
| ---- | ------ |
| `--check` / `--no-check` | Run the normative/IANA consistency check. Default: **on**. |
| `--generate` | With `--check`, also include ready-to-paste IANA markup for every `MISSING IN IANA` issue (see [Generated output](#generated-output)). |
| `--iana-out PATH` | Write the consistency report to `PATH` instead of stdout. |
| `--yaml-out PATH` | Write the full structured object model to `PATH` as YAML (see [YAML export](#yaml-export)). |
| `--self-test` | Run the in-file test suite and exit; ignores every other flag. |

`--check` and `--yaml-out` are independent: either, both, or neither may be
requested in a single invocation. Running with no flags reproduces the
original behaviour (consistency report to stdout, `--check` on by default).

Exit code 0 = no errors (or `--no-check`); exit code 1 = at least one
consistency error. Orphan-prose warnings (see below) are printed to stderr
after all requested output and never affect the exit code.

---

## Error codes

### Object level

| Code | Meaning |
| ---- | ------- |
| `[MISSING IN IANA]` | Normative object has no IANA entry |
| `[MISSING IN NORMATIVE]` | IANA entry has no normative object |
| `[ID MISMATCH]` | Same Object Name, different identifier |
| `[NAME MISMATCH]` | Same identifier, different Object Name |
| `[DUPLICATE NORMATIVE]` | Duplicate identifier in normative section |
| `[DUPLICATE IANA]` | Duplicate identifier in IANA section |

### Data-element level (per matched object pair)

| Code | Meaning |
| ---- | ------- |
| `[ELEM MISSING IN IANA]` | Normative element absent from IANA table |
| `[ELEM MISSING IN NORMATIVE]` | IANA table row absent from normative definition |
| `[ELEM NAME MISMATCH]` | Identifier matches, but Element Name differs |
| `[ELEM CARD MISMATCH]` | Identifier matches, but Cardinality differs |
| `[ELEM MUTABILITY MISMATCH]` | Identifier matches, but Mutability differs |
| `[ELEM TYPE MISMATCH]` | Identifier matches, but Data Type differs |
| `[ELEM DESC EMPTY]` | IANA Description cell is blank; normative has a description |

### Operation level (per matched object pair, and for unmatched objects)

| Code | Meaning |
| ---- | ------- |
| `[OP MISSING IN IANA]` | Normative operation has no IANA entry |
| `[OP MISSING IN NORMATIVE]` | IANA operation has no normative entry |
| `[OP MISSING IDENTIFIER]` | Normative operation heading has no `* Identifier:` bullet |
| `[OP DESC EMPTY]` | IANA operation Description field is blank; normative has a description |

Note: `[OP MISSING IDENTIFIER]` is reported even when the parent object itself
is `[MISSING IN IANA]`, so identifier gaps are always surfaced.

### Operation parameter level (per matched operation pair)

| Code | Meaning |
| ---- | ------- |
| `[PARAM MISSING IN IANA]` | Normative parameter absent from IANA Parameters table |
| `[PARAM MISSING IN NORMATIVE]` | IANA parameter row absent from normative definition |
| `[PARAM NAME MISMATCH]` | Identifier matches, but Parameter Name differs |
| `[PARAM CARD MISMATCH]` | Identifier matches, but Cardinality differs |
| `[PARAM TYPE MISMATCH]` | Identifier matches, but Data Type differs |
| `[PARAM DESC EMPTY]` | IANA description cell is blank; normative has a description |

---

## Normative sections parsed

Controlled by `NORMATIVE_TOPLEVEL_SECTIONS`:

```
# Component Objects
# Process Objects
# Domain Name Data Object
# Contact Data Object
# Host Data Object
# Organisation Data Object
# User Object
```

The IANA section begins at `# IANA Considerations` and is excluded from
normative parsing.

---

## Normative document layouts

### Component and Process objects (nested layout)

Introduced by an H2 heading (`## Foo Object`) inside a normative H1 section.
Object header bullets appear at indent 0:

```
* Name: Foo Object
* Identifier: foo
* Description: …
* Data Elements:
  * Element Name           ← 2-space indent
    * Identifier: elemId   ← 4-space indent
    * Cardinality: 1
    * Mutability: read-write
    * Data Type: String
    * Description: …
```

Body extent: from the `* Name:` bullet up to the next H2 or H1 heading
(whichever comes first). This prevents sibling objects within the same H1
section from bleeding into each other.

Operations for Process objects live under a `### Operations` heading with
individual operations as H4 headings:

```
### Operations

#### Create (Transfer Request) {#anchor}

* Identifier: create

The following transient data elements are defined for this operation:

* Param Name
  * Identifier: paramId
  * Cardinality: 0-1
  * Data Type: String
  * Description: …
```

### Data Objects (flat layout)

Introduced by an H1 heading (`# Domain Name Data Object`).
Elements live in a `## Data Elements` sub-section:

```
## Data Elements

* Element Name           ← 0-indent
  * Identifier: elemId   ← 2-space indent
  * Cardinality: 1
  * Mutability: read-write
  * Data Type: String
  * Description: …
```

Operations live under `## Operations`. There are two kinds of H3 sub-section:

**Direct operations** — singular H3 headings (`### Create Operation`):

```
## Operations

### Create Operation

* Identifier: create

In addition, the following transient data element is defined for this operation:

* Param Name
  * Identifier: paramId
  * Cardinality: 0-1
  * Data Type: String
  * Description: …
```

**Overloaded-process group sections** — plural H3 headings whose name ends with
`Operations` (e.g. `### Transfer Operations`, `### Restore Operations`). These
are group containers whose individual operations are H4 headings:

```
### Transfer Operations

#### Transfer Create Operation

* Identifier: transferCreate

In addition, the following transient data element is defined for this operation:

* Transfer Period
  * Identifier: transferPeriod
  * Cardinality: 0-1
  * Data Type: Period Object
  * Description: …
```

H4 operations inside group sections are parsed identically to direct H3
operations — they must have a `* Identifier:` bullet and may have transient
parameters. Operations missing the identifier bullet are recorded as
`[OP MISSING IDENTIFIER]`.

`### Restore Operations` sections that contain no H4 headings (pure
cross-reference prose) produce no operations and no errors.

### Operation identifier requirement

Every operation heading MUST contain a `* Identifier: <id>` bullet directly
inside the heading block. Operations missing this bullet are recorded and
reported as `[OP MISSING IDENTIFIER]`. They are excluded from all further
comparisons (IANA matching, parameter checking) but the error is always
emitted, even when the parent object has no IANA entry yet.

### Transient parameters

Parameters are parsed from bullet lists that appear after a line containing
the phrase "transient data element" (case-insensitive). Each parameter bullet
must have at minimum an `* Identifier:` sub-bullet; `* Cardinality:` and
`* Data Type:` are also captured when present.

### Operation body fields (Description / Authorisation / Input / Output)

Every operation's body follows this document's own convention, which
differs from elements/objects:

- **Description** is never a `* Description:` bullet (that form is
  element/object-only) — it is plain prose written directly after
  `* Identifier:`. Every prose paragraph between `* Identifier:` and the
  first recognised field bullet below (or the transient-params marker) is
  the description, newline-joined if there is more than one paragraph.
- **`* Authorisation:`** always has a blank inline value followed by a
  nested bullet list — parsed the same way as a Constraints sub-list (one
  string per top-level bullet, deeper nesting such as "Pull transfer:" /
  "Push transfer:" sub-cases newline-folded into that entry). Its
  indentation is read from the source, not assumed.
- **`* Input:`** / **`* Output:`** are always a single inline value (never a
  list) — captured as plain strings.
- Any prose **after** the last recognised field bullet (e.g. a further
  explanatory paragraph following Authorisation) is NOT part of the
  description — it stays in the operation's `notes`.

---

## IANA section layout

### Object block

```
Object: <identifier>

Object Name: <name>

Object Type: Component | Process | Resource

Description: <text>

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name | Card. | Mutability | Data Type | Description |
| ------------------ | ------------ | ----- | ---------- | --------- | ----------- |
| …                  | …            | …     | …          | …         | …           |

Operations

Operation: <name>

Operation Identifier: <id>

Description: <text>

Parameters
| Identifier | Name | Card. | Data Type | Description |
| ---------- | ---- | ----- | --------- | ----------- |
| …          | …    | …     | …         | …           |
```

One blank line separates every field. Multiple `Operation:` blocks may follow
the `Operations` keyword.

`Parameters: (None)` is used when an operation has no parameters.

`Operation Identifier:` is optional in IANA; if absent the script derives the
identifier as the lower-cased first word of the Operation Name.

### Column header aliases

The script accepts two variants for element identifier/name columns:

| Canonical key | Accepted headers |
| ------------- | ---------------- |
| element identifier | `Element Identifier`, `Identifier` |
| element name | `Element Name`, `Name` |
| cardinality | `Card.`, `Cardinality` |
| mutability | `Mutability` |
| data type | `Data Type` |

---

## Type comparison

Data Type strings are normalised before comparison:

- Leading/trailing and internal whitespace collapsed to a single space
- Spaces around square brackets removed: `Dictionary [Integer]` ≡ `Dictionary[Integer]`

---

## Object type mapping

| Normative H1 section | Object Type in IANA |
| -------------------- | ------------------- |
| `# Component Objects` | `Component` |
| `# Process Objects` | `Process` |
| `# Domain Name Data Object` | `Resource` |
| `# Contact Data Object` | `Resource` |
| `# Host Data Object` | `Resource` |
| `# Organisation Data Object` | `Resource` |
| `# User Object` | `Resource` |

---

## Generated output (`--generate`)

When `--generate` is passed, a `GENERATED IANA MARKUP FOR MISSING ENTRIES`
section is appended to stdout after the error list. It covers:

### Missing objects → full IANA block

A complete block ready to paste into the IANA section, including:
- `Object:` / `Object Name:` / `Object Type:` / `Description:` / `Reference:`
  fields, each separated by a blank line
- `Data Elements` pipe table with auto-sized columns; `Description` column
  filled from the normative `* Description:` attribute
- `Operations` section with one `Operation:` block per normative operation,
  `Description:` filled from normative, and a `Parameters` table (or
  `Parameters: (None)`) with descriptions filled in

Column header style:
- Resource objects: `Identifier` / `Name`
- Component/Process objects: `Element Identifier` / `Element Name`

### Missing elements → single table row

One pipe-table row per missing element, with the `Description` cell filled
from the normative `* Description:` attribute:
```
| identifier | Name | Card. | Mutability | Data Type | Description text |
```

### Empty element descriptions → single corrected row (`[ELEM DESC EMPTY]`)

When the IANA table row exists but its Description cell is blank and the
normative definition has a description, a corrected row is output (same
format as for missing elements).

### Missing operations → full operation block

A complete `Operation:` block with `Operation Identifier:`, `Description:`
filled from the normative `* Description:` bullet, and a `Parameters` table
(or `Parameters: (None)`) with descriptions filled in.

### Empty operation descriptions → full corrected block (`[OP DESC EMPTY]`)

When the IANA operation exists but its `Description:` field is blank and the
normative definition has a description, the full corrected operation block is
output (same format as for missing operations).

### Missing parameters → single table row

One pipe-table row per missing parameter, with the `Description` cell filled
from the normative `* Description:` attribute:
```
| identifier | Name | Card. | Data Type | Description text |
```

### Empty parameter descriptions → single corrected row (`[PARAM DESC EMPTY]`)

When the IANA parameter row exists but its Description cell is blank and the
normative definition has a description, a corrected row is output (same
format as for missing parameters).

---

## Orphan prose extraction

Beyond the recognised structured attributes (Name, Identifier, Cardinality,
Mutability, Data Type, Description, Constraints), the draft contains free-form
explanatory prose written directly into object/element/operation blocks
instead of a structured bullet — section intros, operation-body explanations,
numbered lists, etc. `extract_orphan_prose()` is the single function that
collects this text everywhere it can occur, so it is preserved (for
`--yaml-out`) rather than silently dropped.

A line is orphan prose if it is **not**: blank, a heading, a table row
(`| ... |`), a recognised `* Key: value` attribute bullet (see
`_KNOWN_ATTR_KEYS` in the script), an element/operation/parameter header
bullet, or an `A>` aside note. Aside notes are recognised and always dropped
— never captured, never warned about — since they are editorial TODO/TBD/TBC
markers, not spec content.

Consecutive non-blank orphan lines are joined with a single space into one
paragraph string; a blank line starts a new paragraph. This means a wrapped
sentence spanning several source lines becomes one YAML string, and an
unspaced numbered list (no blank lines between items) is joined into a single
paragraph too — if that produces an unwanted merge, add blank lines between
the list items at the source.

### Attachment points

| Extraction site | Target field | Line range |
| --- | --- | --- |
| `parse_section_notes()` | top-level `section_notes[<h1 heading text>]` | from just after the H1 heading to the first object inside it |
| `parse_normative_objects()` | `ObjectDef.preamble` | from the end of the object's header attribute bullets to its first element/operation |
| `_parse_normative_elements_nested()` / `_parse_normative_elements_flat()` | `ElementDef.notes` | from just after the element header bullet to the next element (or block end) |
| `_parse_normative_operations_nested()` | `OperationDef.notes` | the operation body, excluding the parsed parameter bullet sub-range |
| `_parse_normative_params_from_bullets()` | `ParamDef.notes` | from just after the parameter header bullet to the next parameter (or block end) |

### Warnings

Every non-empty extraction is appended to the module-level `PROSE_WARNINGS`
list. `main()` prints all accumulated warnings to stderr after the requested
report/YAML output, one line per orphan-prose occurrence, naming the source
line and how many paragraphs were found. This is intentional: an orphan-prose
warning signals prose that likely belongs in a proper `* Description:` or
`* Constraints:` bullet at the source, and the warning is a nudge to fix the
draft — the YAML export having a populated `notes`/`preamble` field is not
itself an error, only a signal worth reviewing.

---

## YAML export

`--yaml-out PATH` writes the full structured **normative** object model (not
the IANA registry tables — those are checked for consistency against this
model by `--check`, not re-exported) to `PATH` as YAML.

### Structure

Top-level keys: `section_notes`, `components`, `processes`, `resources`.
`components`/`processes`/`resources` each hold a list of objects, keyed by
`ObjectDef.obj_type` via `OBJ_TYPE_TO_YAML_KEY`. Each object dict:

```yaml
identifier: domainName
name: Domain Name Data Object
object_type: Resource
description: "..."
preamble: []              # orphan prose before the first element/operation
elements:
  - identifier: name
    name: Name
    cardinality: "1"
    mutability: create-only
    data_type: String
    description: "..."
    constraints: "..."
    notes: []              # orphan prose inside this element's own block
operations:
  - identifier: create
    name: Create Operation
    description: "..."
    notes: []              # orphan prose in the operation body
    params:
      - identifier: ...
        name: ...
        cardinality: "..."
        data_type: "..."
        description: "..."
        constraints: "..."
        notes: []
```

Nothing in the structured fields is duplicated into `notes`/`preamble`/
`section_notes` and vice versa — those three fields hold only the leftover
prose `extract_orphan_prose()` could not attribute to a recognised bullet.

### Header comment

The YAML file begins with a verbose comment block loaded verbatim from
[object_model_template.yaml](object_model_template.yaml) (`render_yaml()`
reads every leading `#`/blank line from that file and prepends it to the
rendered data). Update that template file, not a Python string literal, when
the schema changes — it is the schema documentation shown to anyone reading
the generated YAML.

### Dependency

`--yaml-out` requires PyYAML (`import yaml`). If unavailable, `render_yaml()`
prints an install instruction (`pip install pyyaml`) to stderr and exits 1.
`--check` alone has no PyYAML dependency.

---

## Self-tests

The script has no separate test files. `_test_*` functions collected in the
`_SELF_TESTS` list at the bottom of `check_iana_consistency.py` are the sole
verification mechanism, run via:

```bash
python3 ../.scripts/check_iana_consistency.py --self-test
```

`--self-test` ignores every other flag. Coverage includes: Constraints
parsing for nested and flat element layouts, orphan-prose extraction
(paragraph joining, aside skipping, empty-when-fully-structured), Organisation/
User section recognition, an end-to-end check that the real draft's
`organisation`/`user` objects parse, YAML model structure, and a YAML
round-trip (render → `yaml.safe_load` → verify).

When changing parsing behaviour or the YAML schema, add or update a `_test_*`
function in the same change — do not verify by hand-running the script and
eyeballing output only, and never create a separate throwaway script to
check behaviour (per [.scripts/CLAUDE.md](CLAUDE.md)).
