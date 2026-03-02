#!/usr/bin/env python3
"""
Verify consistency between normative object definitions and IANA registry tables
in the RPP data-objects draft.

Checks performed
----------------
Object level:
  [MISSING IN IANA]      – normative object has no IANA entry
  [MISSING IN NORMATIVE] – IANA entry has no normative object
  [ID MISMATCH]          – same Object Name, different identifier
  [NAME MISMATCH]        – same identifier, different Object Name
  [DUPLICATE …]          – duplicate identifier within one section

Data-element level:
  [ELEM MISSING IN IANA]      – normative element absent from IANA table
  [ELEM MISSING IN NORMATIVE] – IANA table row absent from normative definition
  [ELEM NAME MISMATCH]        – identifier matches, but Element Name differs
  [ELEM CARD MISMATCH]        – identifier matches, but Cardinality differs
  [ELEM MUTABILITY MISMATCH]  – identifier matches, but Mutability differs
  [ELEM TYPE MISMATCH]        – identifier matches, but Data Type differs
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DRAFT_FILE = Path("./draft-kowalik-rpp-data-objects.md")

NORMATIVE_TOPLEVEL_SECTIONS = [
    "# Component Objects",
    "# Process Objects",
    "# Domain Name Data Object",
    "# Contact Data Object",
    "# Host Data Object",
]

IANA_SECTION_MARKER = "# IANA Considerations"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ElementDef:
    identifier: str
    name: str
    cardinality: str
    mutability: str
    data_type: str
    line: int  # 1-based line number


@dataclass
class ObjectDef:
    name: str
    identifier: str
    source: str        # "normative" or "iana"
    line: int          # 1-based line of the Name / "Object:" declaration
    elements: list[ElementDef] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TOP_LEVEL_NAME_RE  = re.compile(r"^\* Name:\s*(.+)$")
TOP_LEVEL_IDENT_RE = re.compile(r"^\* Identifier:\s*(\S+)")

_WS_RE        = re.compile(r"\s+")
_BRACKET_L_RE = re.compile(r"\s*\[\s*")   # optional space before/inside [
_BRACKET_R_RE = re.compile(r"\s*\]\s*")   # optional space before/inside ]


def _norm(value: str) -> str:
    """Collapse internal whitespace and strip edges for comparison."""
    return _WS_RE.sub(" ", value).strip()


def _norm_type(value: str) -> str:
    """
    Normalise a Data Type string for comparison:
    - collapse whitespace
    - remove spaces around square brackets: "Dictionary [Integer]" == "Dictionary[Integer]"
    """
    v = _norm(value)
    v = _BRACKET_L_RE.sub("[", v)
    v = _BRACKET_R_RE.sub("]", v)
    return v


def _parse_table_row(line: str) -> list[str] | None:
    """
    Parse a GFM pipe-table row.
    Returns a list of stripped cell strings, or None for separator rows.
    """
    line = line.strip()
    if not line.startswith("|"):
        return None
    # Separator row: | --- | --- |
    if re.match(r"^\|[-| :]+\|$", line):
        return None
    cells = line.split("|")
    # strip leading/trailing empty strings produced by the surrounding pipes
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return [c.strip() for c in cells] if cells else None


def in_normative_section(current_h1: str | None) -> bool:
    if current_h1 is None:
        return False
    for marker in NORMATIVE_TOPLEVEL_SECTIONS:
        if current_h1.startswith(marker):
            return True
    return False


# ---------------------------------------------------------------------------
# Normative element parser
# ---------------------------------------------------------------------------

def _collect_element_attrs(lines: list[str], start: int, end: int,
                            indent: int) -> dict[str, tuple[str, int]]:
    """
    Collect attribute bullets at exactly *indent* spaces of indentation.
    Returns {attr_key_lower: (value, 1-based-line)}.
    Stops when a shallower-indented non-blank line is encountered.
    """
    attr_re = re.compile(r"^" + " " * indent + r"\* ([\w /]+):\s*(.*)$")
    attrs: dict[str, tuple[str, int]] = {}
    for j in range(start, end):
        raw = lines[j]
        m = attr_re.match(raw)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            attrs[key] = (val, j + 1)
        elif raw.strip() == "":
            continue
        elif not raw.startswith(" " * indent):
            # stepped back to shallower indent – stop
            break
    return attrs


def _parse_normative_elements_nested(lines: list[str], body_start: int,
                                     body_end: int) -> list[ElementDef]:
    """
    Component / Process object layout:

      * Data Elements:          ← 0-indent
        * Element Name          ← 2-space indent  (element header)
          * Identifier: foo     ← 4-space indent  (attribute)
          * Cardinality: 1
          * Mutability: read-write
          * Data Type: String
    """
    elements: list[ElementDef] = []
    in_data_elements = False
    i = body_start
    while i < body_end:
        raw = lines[i]

        if raw == "* Data Elements:":
            in_data_elements = True
            i += 1
            continue

        if in_data_elements:
            # Another top-level bullet ends the block
            if re.match(r"^\* \S", raw):
                break

            m_elem = re.match(r"^  \* (.+)$", raw)
            if m_elem:
                elem_name_raw = m_elem.group(1).strip()
                elem_line = i + 1
                attrs = _collect_element_attrs(lines, i + 1, body_end, indent=4)
                elem_id = attrs.get("identifier",  ("", 0))[0]
                card    = attrs.get("cardinality", ("", 0))[0]
                mutab   = attrs.get("mutability",  ("", 0))[0]
                dtype   = attrs.get("data type",   ("", 0))[0]
                id_line = attrs.get("identifier",  ("", elem_line))[1]
                if elem_id:
                    elements.append(ElementDef(
                        identifier=elem_id,
                        name=elem_name_raw,
                        cardinality=card,
                        mutability=mutab,
                        data_type=dtype,
                        line=id_line,
                    ))
        i += 1
    return elements


def _parse_normative_elements_flat(lines: list[str], body_start: int,
                                   body_end: int) -> list[ElementDef]:
    """
    Data Object (domainName, contact, host) layout inside "## Data Elements":

      * Element Name            ← 0-indent  (element header)
        * Identifier: foo       ← 2-space indent  (attribute)
        * Cardinality: 1
        * Mutability: read-write
        * Data Type: String
    """
    elements: list[ElementDef] = []
    i = body_start
    while i < body_end:
        raw = lines[i]

        m_elem = re.match(r"^\* (.+)$", raw)
        if m_elem:
            elem_name_raw = m_elem.group(1).strip()
            # Skip object-header bullets
            if elem_name_raw.startswith("Name:") or elem_name_raw.startswith("Identifier:"):
                i += 1
                continue
            elem_line = i + 1
            attrs = _collect_element_attrs(lines, i + 1, body_end, indent=2)
            elem_id = attrs.get("identifier",  ("", 0))[0]
            card    = attrs.get("cardinality", ("", 0))[0]
            mutab   = attrs.get("mutability",  ("", 0))[0]
            dtype   = attrs.get("data type",   ("", 0))[0]
            id_line = attrs.get("identifier",  ("", elem_line))[1]
            if elem_id:
                elements.append(ElementDef(
                    identifier=elem_id,
                    name=elem_name_raw,
                    cardinality=card,
                    mutability=mutab,
                    data_type=dtype,
                    line=id_line,
                ))
        i += 1
    return elements


# ---------------------------------------------------------------------------
# Normative object parser
# ---------------------------------------------------------------------------

def parse_normative_objects(lines: list[str],
                             iana_start: int) -> list[ObjectDef]:
    objects: list[ObjectDef] = []
    current_h1: str | None = None

    i = 0
    while i < iana_start:
        raw = lines[i]
        stripped = raw.strip()

        # Track current H1
        if re.match(r"^# [^#]", stripped):
            current_h1 = stripped

        if not in_normative_section(current_h1):
            i += 1
            continue

        m_name = TOP_LEVEL_NAME_RE.match(raw)
        if not m_name:
            i += 1
            continue

        obj_name = m_name.group(1).strip()
        obj_line = i + 1
        obj_id = ""
        for j in range(i + 1, min(i + 6, iana_start)):
            m_id = TOP_LEVEL_IDENT_RE.match(lines[j])
            if m_id:
                obj_id = m_id.group(1).strip()
                break
            if (lines[j].strip() and
                    not lines[j].startswith(" ") and
                    re.match(r"^\* ", lines[j]) and
                    not TOP_LEVEL_IDENT_RE.match(lines[j])):
                break

        if not obj_id:
            i += 1
            continue

        # Body extent: up to the next H1 heading or iana_start.
        # We stop at H1 only so that H2 sub-sections (## Data Elements,
        # ## Operations, …) within the same object block stay in range.
        body_end = iana_start
        for k in range(i + 1, iana_start):
            if re.match(r"^# [^#]", lines[k].strip()):
                body_end = k
                break

        # Choose parser:
        #   nested  – Component/Process objects use "* Data Elements:" at indent 0
        #   flat    – Data Objects have a "## Data Elements" sub-section with
        #             top-level element bullets
        # Limit the look-ahead to the current object's own bullet block: stop
        # at the next H2 heading so we don't peek into a sibling object.
        nested_search_end = body_end
        for k in range(i + 1, body_end):
            if re.match(r"^## [^#]", lines[k].strip()):
                nested_search_end = k
                break
        is_nested = any(
            lines[k] == "* Data Elements:"
            for k in range(i, nested_search_end)
        )
        if is_nested:
            elements = _parse_normative_elements_nested(lines, i, body_end)
        else:
            # Locate the "## Data Elements" sub-section start and end.
            # The section ends at the next H2 (e.g. "## Operations").
            data_elem_start = body_end  # default: not found → no elements
            data_elem_end   = body_end
            for k in range(i, body_end):
                if re.match(r"^## Data Elements\s*$", lines[k].strip()):
                    data_elem_start = k + 1
                    # Find the end of this sub-section (next H2 or H1)
                    for m in range(k + 1, body_end):
                        if re.match(r"^#{1,2} [^#]", lines[m].strip()):
                            data_elem_end = m
                            break
                    break
            elements = _parse_normative_elements_flat(
                lines, data_elem_start, data_elem_end)

        objects.append(ObjectDef(
            name=obj_name,
            identifier=obj_id,
            source="normative",
            line=obj_line,
            elements=elements,
        ))
        i += 1

    return objects


# ---------------------------------------------------------------------------
# IANA object parser
# ---------------------------------------------------------------------------

def parse_iana_objects(lines: list[str], iana_start: int) -> list[ObjectDef]:
    objects: list[ObjectDef] = []
    i = iana_start

    while i < len(lines):
        raw = lines[i].rstrip()

        m_obj = re.match(r"^Object:\s*(\S+)\s*$", raw)
        if not m_obj:
            i += 1
            continue

        obj_id   = m_obj.group(1).strip()
        obj_line = i + 1
        obj_name = ""

        j = i + 1
        while j < min(i + 6, len(lines)):
            m_n = re.match(r"^Object Name:\s*(.+)$", lines[j].rstrip())
            if m_n:
                obj_name = m_n.group(1).strip()
                break
            j += 1

        if not obj_name:
            i += 1
            continue

        # Scan forward for the "Data Elements" table
        elements: list[ElementDef] = []
        k = i + 1
        in_table = False
        header_cols: list[str] = []

        # Column name aliases → canonical key.
        # Some tables use "Element Identifier" / "Element Name", others use
        # the shorter "Identifier" / "Name" (e.g. domainName, host tables).
        COL_ALIASES: dict[str, list[str]] = {
            "element identifier": ["element identifier", "identifier"],
            "element name":       ["element name", "name"],
            "cardinality":        ["card.", "cardinality"],
            "mutability":         ["mutability"],
            "data type":          ["data type"],
        }

        while k < len(lines):
            rk = lines[k].rstrip()

            # Next "Object:" entry marks end of this block
            if re.match(r"^Object:\s*\S+\s*$", rk) and k > i + 1:
                break

            if not in_table:
                if rk.strip() == "Data Elements":
                    in_table = True
                    header_cols = []
            else:
                cells = _parse_table_row(rk)
                if cells is None:
                    # Non-table line ends the table
                    if rk.strip() and not rk.strip().startswith("|"):
                        in_table = False
                    k += 1
                    continue

                if not header_cols:
                    # First real row = header
                    header_cols = [_norm(c).lower() for c in cells]
                    k += 1
                    continue

                # Data row
                def _col(canonical: str) -> str:
                    for alias in COL_ALIASES.get(canonical, [canonical]):
                        try:
                            idx = header_cols.index(alias)
                            return cells[idx] if idx < len(cells) else ""
                        except ValueError:
                            pass
                    return ""

                elem_id   = _col("element identifier")
                elem_name = _col("element name")
                card      = _col("cardinality")
                mutab     = _col("mutability")
                dtype     = _col("data type")

                if elem_id:
                    elements.append(ElementDef(
                        identifier=elem_id,
                        name=elem_name,
                        cardinality=card,
                        mutability=mutab,
                        data_type=dtype,
                        line=k + 1,
                    ))
            k += 1

        objects.append(ObjectDef(
            name=obj_name,
            identifier=obj_id,
            source="iana",
            line=obj_line,
            elements=elements,
        ))
        i = k

    return objects


# ---------------------------------------------------------------------------
# Consistency checks
# ---------------------------------------------------------------------------

def check_objects(normative: list[ObjectDef],
                  iana: list[ObjectDef]) -> list[str]:
    errors: list[str] = []

    iana_by_id   = {o.identifier: o for o in iana}
    iana_by_name = {o.name: o for o in iana}
    norm_ids     = {o.identifier for o in normative}
    norm_by_name = {o.name: o for o in normative}

    for obj in normative:
        if obj.identifier not in iana_by_id:
            if obj.name in iana_by_name:
                iana_obj = iana_by_name[obj.name]
                errors.append(
                    f"[ID MISMATCH] name='{obj.name}':\n"
                    f"  normative (line {obj.line}):  identifier='{obj.identifier}'\n"
                    f"  IANA     (line {iana_obj.line}): identifier='{iana_obj.identifier}'"
                )
            else:
                errors.append(
                    f"[MISSING IN IANA] normative object at line {obj.line}: "
                    f"identifier='{obj.identifier}', name='{obj.name}'"
                )
            continue

        iana_obj = iana_by_id[obj.identifier]
        if iana_obj.name != obj.name:
            errors.append(
                f"[NAME MISMATCH] identifier='{obj.identifier}':\n"
                f"  normative (line {obj.line}):  name='{obj.name}'\n"
                f"  IANA     (line {iana_obj.line}): name='{iana_obj.name}'"
            )

    for obj in iana:
        if obj.identifier not in norm_ids:
            if obj.name in norm_by_name:
                continue  # already reported as [ID MISMATCH]
            errors.append(
                f"[MISSING IN NORMATIVE] IANA object at line {obj.line}: "
                f"identifier='{obj.identifier}', name='{obj.name}'"
            )

    seen: dict[str, int] = {}
    for obj in normative:
        if obj.identifier in seen:
            errors.append(
                f"[DUPLICATE NORMATIVE] identifier='{obj.identifier}' "
                f"at lines {seen[obj.identifier]} and {obj.line}."
            )
        seen[obj.identifier] = obj.line

    seen = {}
    for obj in iana:
        if obj.identifier in seen:
            errors.append(
                f"[DUPLICATE IANA] identifier='{obj.identifier}' "
                f"at lines {seen[obj.identifier]} and {obj.line}."
            )
        seen[obj.identifier] = obj.line

    return errors


def check_elements(norm_obj: ObjectDef, iana_obj: ObjectDef) -> list[str]:
    errors: list[str] = []
    prefix = f"object '{norm_obj.identifier}'"

    iana_elems = {e.identifier: e for e in iana_obj.elements}
    norm_elems = {e.identifier: e for e in norm_obj.elements}

    for ne in norm_obj.elements:
        if ne.identifier not in iana_elems:
            errors.append(
                f"[ELEM MISSING IN IANA] {prefix}: "
                f"element '{ne.identifier}' ('{ne.name}') at normative line {ne.line} "
                f"has no row in the IANA table."
            )
            continue

        ie = iana_elems[ne.identifier]
        if _norm(ne.name) != _norm(ie.name):
            errors.append(
                f"[ELEM NAME MISMATCH] {prefix}, element '{ne.identifier}':\n"
                f"    normative (line {ne.line}):  name='{ne.name}'\n"
                f"    IANA     (line {ie.line}): name='{ie.name}'"
            )
        if _norm(ne.cardinality) != _norm(ie.cardinality):
            errors.append(
                f"[ELEM CARD MISMATCH] {prefix}, element '{ne.identifier}':\n"
                f"    normative (line {ne.line}):  cardinality='{ne.cardinality}'\n"
                f"    IANA     (line {ie.line}): cardinality='{ie.cardinality}'"
            )
        if _norm(ne.mutability) != _norm(ie.mutability):
            errors.append(
                f"[ELEM MUTABILITY MISMATCH] {prefix}, element '{ne.identifier}':\n"
                f"    normative (line {ne.line}):  mutability='{ne.mutability}'\n"
                f"    IANA     (line {ie.line}): mutability='{ie.mutability}'"
            )
        if _norm_type(ne.data_type) != _norm_type(ie.data_type):
            errors.append(
                f"[ELEM TYPE MISMATCH] {prefix}, element '{ne.identifier}':\n"
                f"    normative (line {ne.line}):  data_type='{ne.data_type}'\n"
                f"    IANA     (line {ie.line}): data_type='{ie.data_type}'"
            )

    for ie in iana_obj.elements:
        if ie.identifier not in norm_elems:
            errors.append(
                f"[ELEM MISSING IN NORMATIVE] {prefix}: "
                f"IANA table row '{ie.identifier}' ('{ie.name}') at line {ie.line} "
                f"has no matching normative element definition."
            )

    return errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_document(path: Path) -> tuple[list[ObjectDef], list[ObjectDef]]:
    lines = path.read_text().splitlines()

    iana_start = None
    for i, line in enumerate(lines):
        if line.strip() == IANA_SECTION_MARKER:
            iana_start = i
            break
    if iana_start is None:
        print(f"ERROR: '{IANA_SECTION_MARKER}' not found.", file=sys.stderr)
        sys.exit(1)

    normative = parse_normative_objects(lines, iana_start)
    iana      = parse_iana_objects(lines, iana_start)
    return normative, iana


def main() -> int:
    if not DRAFT_FILE.exists():
        print(f"ERROR: file not found: {DRAFT_FILE}", file=sys.stderr)
        return 1

    normative, iana = parse_document(DRAFT_FILE)

    print(f"Normative objects found ({len(normative)}):")
    for o in normative:
        print(f"  line {o.line:4d}  id={o.identifier!r:30s}  name={o.name!r}"
              f"  elements={len(o.elements)}")

    print(f"\nIANA objects found ({len(iana)}):")
    for o in iana:
        print(f"  line {o.line:4d}  id={o.identifier!r:30s}  name={o.name!r}"
              f"  elements={len(o.elements)}")

    errors = check_objects(normative, iana)

    iana_by_id = {o.identifier: o for o in iana}
    for norm_obj in normative:
        iana_obj = iana_by_id.get(norm_obj.identifier)
        if iana_obj is not None:
            errors.extend(check_elements(norm_obj, iana_obj))

    print()
    if errors:
        print(f"CONSISTENCY ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: all normative object and element definitions match their IANA entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
