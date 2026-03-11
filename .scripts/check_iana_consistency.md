# check_iana_consistency.py — Specification and Processing Rules

## Purpose

Programmatically verifies consistency between the normative object definitions
and the IANA registry tables in `src/draft-kowalik-rpp-data-objects.md`.

## Usage

Run from the `src/` directory:

```bash
cd src
python3 ../.scripts/check_iana_consistency.py [--generate]
```

`--generate` — in addition to reporting errors, print ready-to-paste IANA
markup for every `MISSING IN IANA` issue (see [Generated output](#generated-output)).

Exit code 0 = no errors; exit code 1 = at least one consistency error.

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

### Operation level (per matched object pair, and for unmatched objects)

| Code | Meaning |
| ---- | ------- |
| `[OP MISSING IN IANA]` | Normative operation has no IANA entry |
| `[OP MISSING IN NORMATIVE]` | IANA operation has no normative entry |
| `[OP MISSING IDENTIFIER]` | Normative operation heading has no `* Identifier:` bullet |

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

---

## Normative sections parsed

Controlled by `NORMATIVE_TOPLEVEL_SECTIONS`:

```
# Component Objects
# Process Objects
# Domain Name Data Object
# Contact Data Object
# Host Data Object
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

---

## Generated output (`--generate`)

When `--generate` is passed, a `GENERATED IANA MARKUP FOR MISSING ENTRIES`
section is appended to stdout after the error list. It covers:

### Missing objects → full IANA block

A complete block ready to paste into the IANA section, including:
- `Object:` / `Object Name:` / `Object Type:` / `Description:` / `Reference:`
  fields, each separated by a blank line
- `Data Elements` pipe table with auto-sized columns and a `Description` column
  (empty cells to be filled in)
- `Operations` section with one `Operation:` block per normative operation,
  including a `Parameters` table or `Parameters: (None)`

Column header style:
- Resource objects: `Identifier` / `Name`
- Component/Process objects: `Element Identifier` / `Element Name`

### Missing elements → single table row

One pipe-table row per missing element, formatted as:
```
| identifier | Name | Card. | Mutability | Data Type |  |
```

### Missing operations → full operation block

A complete `Operation:` block with `Operation Identifier:`, empty
`Description:`, and a `Parameters` table (or `Parameters: (None)`).

### Missing parameters → single table row

One pipe-table row per missing parameter:
```
| identifier | Name | Card. | Data Type |  |
```
