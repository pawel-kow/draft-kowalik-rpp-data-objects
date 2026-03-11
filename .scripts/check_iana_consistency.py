#!/usr/bin/env python3
"""
Verify consistency between normative object definitions and IANA registry tables
in the RPP data-objects draft.

Checks performed
----------------
Object level:
  [MISSING IN IANA]      - normative object has no IANA entry
  [MISSING IN NORMATIVE] - IANA entry has no normative object
  [ID MISMATCH]          - same Object Name, different identifier
  [NAME MISMATCH]        - same identifier, different Object Name
  [DUPLICATE …]          - duplicate identifier within one section

Data-element level:
  [ELEM MISSING IN IANA]      - normative element absent from IANA table
  [ELEM MISSING IN NORMATIVE] - IANA table row absent from normative definition
  [ELEM NAME MISMATCH]        - identifier matches, but Element Name differs
  [ELEM CARD MISMATCH]        - identifier matches, but Cardinality differs
  [ELEM MUTABILITY MISMATCH]  - identifier matches, but Mutability differs
  [ELEM TYPE MISMATCH]        - identifier matches, but Data Type differs

Operation level:
  [OP MISSING IN IANA]      - normative operation has no IANA entry
  [OP MISSING IN NORMATIVE] - IANA operation has no normative entry
  [OP NAME MISMATCH]        - same identifier, different Operation Name

Operation parameter level:
  [PARAM MISSING IN IANA]      - normative parameter absent from IANA table
  [PARAM MISSING IN NORMATIVE] - IANA parameter row absent from normative
  [PARAM NAME MISMATCH]        - identifier matches, but Parameter Name differs
  [PARAM CARD MISMATCH]        - identifier matches, but Cardinality differs
  [PARAM TYPE MISMATCH]        - identifier matches, but Data Type differs
"""

import argparse
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

# Map H1 section prefix → Object Type label used in IANA tables
SECTION_TO_OBJ_TYPE: dict[str, str] = {
    "# Component Objects": "Component",
    "# Process Objects":   "Process",
    "# Domain Name Data Object": "Resource",
    "# Contact Data Object":     "Resource",
    "# Host Data Object":        "Resource",
}


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
class ParamDef:
    """Operation parameter (transient, not persisted)."""
    identifier: str
    name: str
    cardinality: str
    data_type: str
    line: int  # 1-based line number


@dataclass
class OperationDef:
    name: str          # human-readable name (e.g. "Create", "Read")
    identifier: str    # machine-readable id (e.g. "create", "read")
    line: int          # 1-based line number
    params: list[ParamDef] = field(default_factory=list)


@dataclass
class ObjectDef:
    name: str
    identifier: str
    source: str        # "normative" or "iana"
    line: int          # 1-based line of the Name / "Object:" declaration
    obj_type: str = ""       # "Component", "Process", or "Resource"
    description: str = ""
    elements: list[ElementDef] = field(default_factory=list)
    operations: list[OperationDef] = field(default_factory=list)


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
            # stepped back to shallower indent - stop
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
# Normative operation parser
# ---------------------------------------------------------------------------

def _parse_normative_params_from_bullets(lines: list[str], start: int,
                                         end: int) -> list[ParamDef]:
    """
    Parse transient operation parameters from a bullet block.
    Used for both nested (Process, 4-space attrs) and flat (Data Object, 2-space attrs).

    Nested (Process objects – params live inside the #### heading block):
      * Param Name              ← 0-indent
        * Identifier: foo       ← 2-space indent
        * Cardinality: 0-1
        * Data Type: String

    The function tries 2-space attrs first and falls back to 4-space if not found.
    """
    params: list[ParamDef] = []
    i = start
    while i < end:
        raw = lines[i]
        m_param = re.match(r"^\* (.+)$", raw)
        if m_param:
            param_name_raw = m_param.group(1).strip()
            # Skip bullet lines that are not parameter headers
            if re.match(r"^(Identifier|Cardinality|Data Type|Mutability|"
                        r"Input|Output|Authorisation|Constraints|Description|"
                        r"In EPP):", param_name_raw):
                i += 1
                continue
            param_line = i + 1
            # Try 2-space indent first, then 4-space
            attrs = _collect_element_attrs(lines, i + 1, end, indent=2)
            if not attrs.get("identifier"):
                attrs = _collect_element_attrs(lines, i + 1, end, indent=4)
            param_id = attrs.get("identifier",  ("", 0))[0]
            card     = attrs.get("cardinality", ("", 0))[0]
            dtype    = attrs.get("data type",   ("", 0))[0]
            id_line  = attrs.get("identifier",  ("", param_line))[1]
            if param_id:
                params.append(ParamDef(
                    identifier=param_id,
                    name=param_name_raw,
                    cardinality=card,
                    data_type=dtype,
                    line=id_line,
                ))
        i += 1
    return params


def _parse_normative_operations_nested(lines: list[str],
                                       ops_start: int,
                                       ops_end: int,
                                       heading_re: re.Pattern) -> list[OperationDef]:
    """
    Parse operations from a heading-based block.

    heading_re matches the operation heading line (e.g. "#### Create {#...}")
    and capture group 1 must be the operation name.

    Within each operation block, `* Identifier: <id>` provides the machine id.
    Operations without a `* Identifier:` bullet are recorded with identifier=""
    so that callers can report them as [OP MISSING IDENTIFIER].
    Transient params are bullet items after a "following transient" marker.
    """
    operations: list[OperationDef] = []
    i = ops_start
    while i < ops_end:
        raw = lines[i].rstrip()
        m_heading = heading_re.match(raw)
        if not m_heading:
            i += 1
            continue

        op_name = m_heading.group(1).strip()
        op_line = i + 1
        op_id   = ""

        # Find end of this operation block (next same-level heading or ops_end)
        heading_prefix = raw[:raw.index(" ")]  # e.g. "####" or "###"
        block_end = ops_end
        for k in range(i + 1, ops_end):
            stripped = lines[k].rstrip()
            if re.match(r"^#{1,6} ", stripped):
                other_prefix = stripped[:stripped.index(" ")]
                if len(other_prefix) <= len(heading_prefix):
                    block_end = k
                    break

        # Scan for * Identifier: within the block
        for j in range(i + 1, block_end):
            m_id = re.match(r"^\* Identifier:\s*(\S+)", lines[j])
            if m_id:
                op_id = m_id.group(1).strip()
                break

        # Find params: look for "transient data element" marker, then parse bullets
        params: list[ParamDef] = []
        param_start = block_end
        for j in range(i + 1, block_end):
            if re.search(r"transient data element", lines[j], re.IGNORECASE):
                param_start = j + 1
                break

        if param_start < block_end:
            params = _parse_normative_params_from_bullets(
                lines, param_start, block_end)

        # Always record the operation; identifier="" signals missing identifier
        operations.append(OperationDef(
            name=op_name,
            identifier=op_id,
            line=op_line,
            params=params,
        ))
        i = block_end  # jump past this block to avoid re-scanning

    return operations


def _parse_normative_operations_for_object(lines: list[str],
                                           obj_start: int,
                                           obj_end: int,
                                           is_nested: bool) -> list[OperationDef]:
    """
    Locate the Operations sub-section for an object and parse its operations.

    Data Objects (Resource):
      ## Operations          ← H2
        ### Create Operation ← H3
          * Identifier: create

    Process Objects (nested bullet layout):
      ### Operations         ← H3
        #### Create {#...}  ← H4
          * Identifier: create
    """
    ops_section_start = obj_end  # default: not found

    if is_nested:
        # Process objects: look for "### Operations" within H2 sub-section
        ops_heading_re = re.compile(r"^### Operations\s*$")
        # H4 headings are individual operations; exclude plural "Operations" reference sections
        ops_op_re      = re.compile(r"^#### (.+?)(?:\s*\{[^}]*\})?\s*$")
    else:
        # Data Objects: look for "## Operations"
        ops_heading_re = re.compile(r"^## Operations\s*$")
        # H3 headings are individual operations; exclude plural "… Operations" reference sections
        # e.g. "### Transfer Operations" / "### Restore Operations" are cross-references, not defs
        ops_op_re      = re.compile(r"^### (?!.*\bOperations\s*$)(.+?)(?:\s*\{[^}]*\})?\s*$")

    for k in range(obj_start, obj_end):
        if ops_heading_re.match(lines[k].strip()):
            ops_section_start = k + 1
            break

    if ops_section_start >= obj_end:
        return []

    return _parse_normative_operations_nested(
        lines, ops_section_start, obj_end, ops_op_re)


# ---------------------------------------------------------------------------
# Normative object parser
# ---------------------------------------------------------------------------

def _obj_type_for_h1(h1: str | None) -> str:
    if h1 is None:
        return ""
    for prefix, obj_type in SECTION_TO_OBJ_TYPE.items():
        if h1.startswith(prefix):
            return obj_type
    return ""


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
        obj_desc = ""
        for j in range(i + 1, min(i + 10, iana_start)):
            m_id = TOP_LEVEL_IDENT_RE.match(lines[j])
            if m_id:
                obj_id = m_id.group(1).strip()
                continue
            m_desc = re.match(r"^\* Description:\s*(.+)$", lines[j])
            if m_desc:
                obj_desc = m_desc.group(1).strip()
                continue
            # Stop at a top-level bullet that isn't a known attribute
            if (lines[j].strip() and
                    not lines[j].startswith(" ") and
                    re.match(r"^\* ", lines[j]) and
                    not TOP_LEVEL_IDENT_RE.match(lines[j]) and
                    not re.match(r"^\* Description:", lines[j]) and
                    not re.match(r"^\* (Object Type|Data Elements|Operations):", lines[j])):
                if obj_id:
                    break

        if not obj_id:
            i += 1
            continue

        # Determine is_nested first with a provisional look-ahead (to next H1).
        # Component/Process objects use "* Data Elements:" bullet at indent 0.
        # Data Objects use a "## Data Elements" sub-section heading.
        provisional_end = iana_start
        for k in range(i + 1, iana_start):
            if re.match(r"^# [^#]", lines[k].strip()):
                provisional_end = k
                break

        nested_search_end = provisional_end
        for k in range(i + 1, provisional_end):
            if re.match(r"^## [^#]", lines[k].strip()):
                nested_search_end = k
                break
        is_nested = any(
            lines[k] == "* Data Elements:"
            for k in range(i, nested_search_end)
        )

        # Now compute the real body_end:
        # - Nested (Component/Process): bounded by next H1 or H2 (sibling object)
        # - Flat (Data Objects):        bounded by next H1 only (they ARE H1 sections)
        body_end = provisional_end
        if is_nested:
            for k in range(i + 1, provisional_end):
                if re.match(r"^## [^#]", lines[k].strip()):
                    body_end = k
                    break
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

        operations = _parse_normative_operations_for_object(
            lines, i, body_end, is_nested)

        objects.append(ObjectDef(
            name=obj_name,
            identifier=obj_id,
            source="normative",
            line=obj_line,
            obj_type=_obj_type_for_h1(current_h1),
            description=obj_desc,
            elements=elements,
            operations=operations,
        ))
        i += 1

    return objects


# ---------------------------------------------------------------------------
# IANA object parser
# ---------------------------------------------------------------------------

def _parse_iana_params_table(lines: list[str], start: int,
                              end: int) -> list[ParamDef]:
    """
    Parse a Parameters pipe-table in the IANA section.
    Columns: Identifier | Name | Card. | Data Type | Description
    """
    params: list[ParamDef] = []
    COL_ALIASES: dict[str, list[str]] = {
        "identifier": ["identifier"],
        "name":       ["name"],
        "cardinality": ["card.", "cardinality"],
        "data type":  ["data type"],
    }
    header_cols: list[str] = []
    i = start
    while i < end:
        rk = lines[i].rstrip()
        cells = _parse_table_row(rk)
        if cells is None:
            if rk.strip() and not rk.strip().startswith("|"):
                break  # non-table line ends table
            i += 1
            continue
        if not header_cols:
            header_cols = [_norm(c).lower() for c in cells]
            i += 1
            continue

        def _col(canonical: str) -> str:
            for alias in COL_ALIASES.get(canonical, [canonical]):
                try:
                    idx = header_cols.index(alias)
                    return cells[idx] if idx < len(cells) else ""
                except ValueError:
                    pass
            return ""

        param_id = _col("identifier")
        if param_id:
            params.append(ParamDef(
                identifier=param_id,
                name=_col("name"),
                cardinality=_col("cardinality"),
                data_type=_col("data type"),
                line=i + 1,
            ))
        i += 1
    return params


def _parse_iana_operations(lines: list[str], ops_start: int,
                            obj_end: int) -> list[OperationDef]:
    """
    Parse operations from the IANA section after the "Operations" keyword.

    Format:
      Operation: <Name>

      Operation Identifier: <id>    ← optional

      Description: ...

      Parameters
      | Identifier | Name | Card. | Data Type | Description |
      | ...        | ...  | ...   | ...       | ...         |

    or:
      Parameters: (None)
    """
    operations: list[OperationDef] = []
    i = ops_start
    while i < obj_end:
        rk = lines[i].rstrip()
        m_op = re.match(r"^Operation:\s*(.+)$", rk)
        if not m_op:
            i += 1
            continue

        op_name = m_op.group(1).strip()
        op_line = i + 1
        op_id   = ""

        # Find end of this operation block (next "Operation:" or obj_end)
        block_end = obj_end
        for k in range(i + 1, obj_end):
            if re.match(r"^Operation:\s*\S", lines[k].rstrip()):
                block_end = k
                break

        # Scan for "Operation Identifier:" within the block
        for j in range(i + 1, block_end):
            m_id = re.match(r"^Operation Identifier:\s*(.+)$", lines[j].rstrip())
            if m_id:
                # Take only the first token (ignore trailing parenthetical)
                op_id = m_id.group(1).strip().split()[0]
                break

        if not op_id:
            # Fall back: derive id from name (lowercase first word)
            op_id = op_name.lower().split()[0]

        # Find "Parameters" keyword and parse table or "(None)"
        params: list[ParamDef] = []
        for j in range(i + 1, block_end):
            rj = lines[j].rstrip()
            if rj.strip() == "Parameters":
                params = _parse_iana_params_table(lines, j + 1, block_end)
                break
            if re.match(r"^Parameters:\s*\(None\)", rj):
                break

        operations.append(OperationDef(
            name=op_name,
            identifier=op_id,
            line=op_line,
            params=params,
        ))
        i = block_end

    return operations


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

        # Determine end of this object block
        obj_end = len(lines)
        for k in range(i + 1, len(lines)):
            if re.match(r"^Object:\s*\S+\s*$", lines[k].rstrip()):
                obj_end = k
                break

        # Scan for "Data Elements" table
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

        ops_start_in_block = obj_end  # position of "Operations" keyword

        while k < obj_end:
            rk = lines[k].rstrip()

            if rk.strip() == "Operations":
                ops_start_in_block = k + 1
                # Stop element scanning
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

        # Parse operations if present
        operations: list[OperationDef] = []
        if ops_start_in_block < obj_end:
            operations = _parse_iana_operations(lines, ops_start_in_block, obj_end)

        objects.append(ObjectDef(
            name=obj_name,
            identifier=obj_id,
            source="iana",
            line=obj_line,
            elements=elements,
            operations=operations,
        ))
        i = obj_end

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


def check_operations(norm_obj: ObjectDef, iana_obj: ObjectDef) -> list[str]:
    errors: list[str] = []
    prefix = f"object '{norm_obj.identifier}'"

    iana_ops  = {op.identifier: op for op in iana_obj.operations}
    # Operations with identifier="" are excluded from id-keyed lookup but
    # reported individually below.
    norm_ops  = {op.identifier: op for op in norm_obj.operations if op.identifier}

    for nop in norm_obj.operations:
        # Report operations that are missing a * Identifier: bullet
        if not nop.identifier:
            errors.append(
                f"[OP MISSING IDENTIFIER] {prefix}: "
                f"operation '{nop.name}' at normative line {nop.line} "
                f"has no '* Identifier:' bullet."
            )
            continue
        if nop.identifier not in iana_ops:
            errors.append(
                f"[OP MISSING IN IANA] {prefix}: "
                f"operation '{nop.identifier}' ('{nop.name}') at normative line {nop.line} "
                f"has no entry in the IANA Operations table."
            )
            continue

        iop = iana_ops[nop.identifier]
        # Name comparison: IANA names often differ stylistically, so only warn
        # when they differ significantly (skip for now — names are informal)

        # Check parameters
        iana_params = {p.identifier: p for p in iop.params}
        norm_params = {p.identifier: p for p in nop.params}

        for np in nop.params:
            if np.identifier not in iana_params:
                errors.append(
                    f"[PARAM MISSING IN IANA] {prefix}, operation '{nop.identifier}': "
                    f"parameter '{np.identifier}' ('{np.name}') at normative line {np.line} "
                    f"has no row in the IANA Parameters table."
                )
                continue
            ip = iana_params[np.identifier]
            if _norm(np.name) != _norm(ip.name):
                errors.append(
                    f"[PARAM NAME MISMATCH] {prefix}, op '{nop.identifier}', "
                    f"param '{np.identifier}':\n"
                    f"    normative (line {np.line}):  name='{np.name}'\n"
                    f"    IANA     (line {ip.line}): name='{ip.name}'"
                )
            if _norm(np.cardinality) != _norm(ip.cardinality):
                errors.append(
                    f"[PARAM CARD MISMATCH] {prefix}, op '{nop.identifier}', "
                    f"param '{np.identifier}':\n"
                    f"    normative (line {np.line}):  cardinality='{np.cardinality}'\n"
                    f"    IANA     (line {ip.line}): cardinality='{ip.cardinality}'"
                )
            if _norm_type(np.data_type) != _norm_type(ip.data_type):
                errors.append(
                    f"[PARAM TYPE MISMATCH] {prefix}, op '{nop.identifier}', "
                    f"param '{np.identifier}':\n"
                    f"    normative (line {np.line}):  data_type='{np.data_type}'\n"
                    f"    IANA     (line {ip.line}): data_type='{ip.data_type}'"
                )

        for ip in iop.params:
            if ip.identifier not in norm_params:
                errors.append(
                    f"[PARAM MISSING IN NORMATIVE] {prefix}, operation '{iop.identifier}': "
                    f"IANA parameter '{ip.identifier}' ('{ip.name}') at line {ip.line} "
                    f"has no matching normative parameter definition."
                )

    for iop in iana_obj.operations:
        if iop.identifier not in norm_ops:
            errors.append(
                f"[OP MISSING IN NORMATIVE] {prefix}: "
                f"IANA operation '{iop.identifier}' ('{iop.name}') at line {iop.line} "
                f"has no matching normative operation definition."
            )

    return errors


# ---------------------------------------------------------------------------
# IANA table generators
# ---------------------------------------------------------------------------

def generate_iana_table(obj: ObjectDef) -> str:
    """
    Generate the full IANA registry block for a normative object that is
    missing from the IANA section.

    Resource objects use shorter column headers (Identifier / Name);
    Component and Process objects use the longer form (Element Identifier /
    Element Name).  All blocks follow the blank-line-separated field format
    used in the existing IANA section.
    """
    is_resource = obj.obj_type == "Resource"
    id_hdr   = "Identifier"   if is_resource else "Element Identifier"
    name_hdr = "Name"         if is_resource else "Element Name"

    out: list[str] = []
    out.append(f"Object: {obj.identifier}")
    out.append("")
    out.append(f"Object Name: {obj.name}")
    out.append("")
    out.append(f"Object Type: {obj.obj_type or 'TBD'}")
    out.append("")
    out.append(f"Description: {obj.description or 'TBD'}")
    out.append("")
    out.append("Reference: [This-ID]")
    out.append("")
    out.append("Data Elements")

    if obj.elements:
        id_w   = max(len(id_hdr),   max(len(e.identifier)  for e in obj.elements))
        name_w = max(len(name_hdr), max(len(e.name)        for e in obj.elements))
        card_w = max(len("Card."),  max(len(e.cardinality) for e in obj.elements))
        mut_w  = max(len("Mutability"), max(len(e.mutability) for e in obj.elements))
        type_w = max(len("Data Type"),  max(len(e.data_type)  for e in obj.elements))

        def _row(id_: str, name: str, card: str, mut: str, dtype: str,
                 desc: str = "") -> str:
            return (f"| {id_:<{id_w}} | {name:<{name_w}} | {card:<{card_w}}"
                    f" | {mut:<{mut_w}} | {dtype:<{type_w}} | {desc} |")

        sep = (f"| {'-' * id_w} | {'-' * name_w} | {'-' * card_w}"
               f" | {'-' * mut_w} | {'-' * type_w} | {'-' * len('Description')} |")

        out.append(_row(id_hdr, name_hdr, "Card.", "Mutability", "Data Type",
                        "Description"))
        out.append(sep)
        for e in obj.elements:
            out.append(_row(e.identifier, e.name, e.cardinality,
                            e.mutability, e.data_type))
    else:
        out.append(f"| {id_hdr} | {name_hdr} | Card. | Mutability | Data Type | Description |")
        out.append(f"| {'-' * len(id_hdr)} | {'-' * len(name_hdr)} | ----- | ---------- | --------- | ----------- |")

    # Operations section
    if obj.operations:
        out.append("")
        out.append("Operations")
        for op in obj.operations:
            out.append("")
            out.append(f"Operation: {op.name}")
            out.append("")
            out.append(f"Operation Identifier: {op.identifier}")
            out.append("")
            out.append("Description: ")
            out.append("")
            if op.params:
                pid_w  = max(len("Identifier"), max(len(p.identifier) for p in op.params))
                pnm_w  = max(len("Name"),       max(len(p.name)       for p in op.params))
                pcd_w  = max(len("Card."),      max(len(p.cardinality) for p in op.params))
                pty_w  = max(len("Data Type"),  max(len(p.data_type)   for p in op.params))

                def _prow(id_: str, name: str, card: str, dtype: str,
                          desc: str = "") -> str:
                    return (f"| {id_:<{pid_w}} | {name:<{pnm_w}} | {card:<{pcd_w}}"
                            f" | {dtype:<{pty_w}} | {desc} |")

                psep = (f"| {'-' * pid_w} | {'-' * pnm_w} | {'-' * pcd_w}"
                        f" | {'-' * pty_w} | {'-' * len('Description')} |")

                out.append("Parameters")
                out.append(_prow("Identifier", "Name", "Card.", "Data Type", "Description"))
                out.append(psep)
                for p in op.params:
                    out.append(_prow(p.identifier, p.name, p.cardinality, p.data_type))
            else:
                out.append("Parameters: (None)")

    return "\n".join(out)


def generate_iana_row(elem: ElementDef) -> str:
    """
    Generate a single IANA table row for a normative element that is missing
    from an existing IANA table.
    """
    return (f"| {elem.identifier} | {elem.name} | {elem.cardinality}"
            f" | {elem.mutability} | {elem.data_type} |  |")


def generate_iana_op_block(op: OperationDef) -> str:
    """
    Generate the IANA operation block for a normative operation that is missing
    from the IANA Operations section.
    """
    out: list[str] = []
    out.append(f"Operation: {op.name}")
    out.append("")
    out.append(f"Operation Identifier: {op.identifier}")
    out.append("")
    out.append("Description: ")
    out.append("")
    if op.params:
        pid_w = max(len("Identifier"), max(len(p.identifier) for p in op.params))
        pnm_w = max(len("Name"),       max(len(p.name)       for p in op.params))
        pcd_w = max(len("Card."),      max(len(p.cardinality) for p in op.params))
        pty_w = max(len("Data Type"),  max(len(p.data_type)   for p in op.params))

        def _prow(id_: str, name: str, card: str, dtype: str,
                  desc: str = "") -> str:
            return (f"| {id_:<{pid_w}} | {name:<{pnm_w}} | {card:<{pcd_w}}"
                    f" | {dtype:<{pty_w}} | {desc} |")

        psep = (f"| {'-' * pid_w} | {'-' * pnm_w} | {'-' * pcd_w}"
                f" | {'-' * pty_w} | {'-' * len('Description')} |")

        out.append("Parameters")
        out.append(_prow("Identifier", "Name", "Card.", "Data Type", "Description"))
        out.append(psep)
        for p in op.params:
            out.append(_prow(p.identifier, p.name, p.cardinality, p.data_type))
    else:
        out.append("Parameters: (None)")
    return "\n".join(out)


def generate_iana_param_row(param: ParamDef) -> str:
    """
    Generate a single IANA Parameters table row for a missing parameter.
    """
    return (f"| {param.identifier} | {param.name} | {param.cardinality}"
            f" | {param.data_type} |  |")


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
    parser = argparse.ArgumentParser(
        description="Check consistency between normative object definitions and IANA tables."
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help=(
            "For every MISSING IN IANA issue, print generated IANA markup: "
            "full table block for missing objects, single row for missing elements, "
            "full operation block for missing operations, single row for missing parameters."
        ),
    )
    args = parser.parse_args()

    if not DRAFT_FILE.exists():
        print(f"ERROR: file not found: {DRAFT_FILE}", file=sys.stderr)
        return 1

    normative, iana = parse_document(DRAFT_FILE)

    print(f"Normative objects found ({len(normative)}):")
    for o in normative:
        print(f"  line {o.line:4d}  id={o.identifier!r:30s}  name={o.name!r}"
              f"  elements={len(o.elements)}  ops={len(o.operations)}")

    print(f"\nIANA objects found ({len(iana)}):")
    for o in iana:
        print(f"  line {o.line:4d}  id={o.identifier!r:30s}  name={o.name!r}"
              f"  elements={len(o.elements)}  ops={len(o.operations)}")

    errors = check_objects(normative, iana)

    iana_by_id  = {o.identifier: o for o in iana}
    elem_errors: list[tuple[ObjectDef, list[str]]] = []
    op_errors:   list[tuple[ObjectDef, list[str]]] = []
    _empty_obj = ObjectDef(name="", identifier="", source="iana", line=0)
    for norm_obj in normative:
        iana_obj = iana_by_id.get(norm_obj.identifier)
        if iana_obj is not None:
            obj_elem_errors = check_elements(norm_obj, iana_obj)
            if obj_elem_errors:
                elem_errors.append((norm_obj, obj_elem_errors))
            errors.extend(obj_elem_errors)

        # check_operations is always run: against the real IANA object when it
        # exists, or against an empty stub when the object is missing from IANA
        # (so that [OP MISSING IDENTIFIER] errors are always surfaced).
        obj_op_errors = check_operations(norm_obj, iana_obj if iana_obj is not None else _empty_obj)
        if obj_op_errors:
            op_errors.append((norm_obj, obj_op_errors))
        errors.extend(obj_op_errors)

    print()
    if errors:
        print(f"CONSISTENCY ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")

        if args.generate:
            print()
            print("=" * 72)
            print("GENERATED IANA MARKUP FOR MISSING ENTRIES")
            print("=" * 72)

            # Missing objects → full table block (incl. operations)
            iana_names = {x.name for x in iana}
            missing_obj_ids = {
                o.identifier for o in normative
                if o.identifier not in iana_by_id and o.name not in iana_names
            }
            for obj in normative:
                if obj.identifier in missing_obj_ids:
                    print()
                    print(f"--- [MISSING IN IANA] object '{obj.identifier}' ---")
                    print()
                    print(generate_iana_table(obj))

            # Missing elements → single row per element
            for norm_obj, obj_errors in elem_errors:
                iana_obj = iana_by_id[norm_obj.identifier]
                iana_elem_ids = {e.identifier for e in iana_obj.elements}
                missing_elems = [
                    e for e in norm_obj.elements
                    if e.identifier not in iana_elem_ids
                ]
                if missing_elems:
                    print()
                    print(f"--- [ELEM MISSING IN IANA] object '{norm_obj.identifier}' ---")
                    for elem in missing_elems:
                        print(generate_iana_row(elem))

            # Missing operations → full operation block
            for norm_obj, obj_errors in op_errors:
                iana_obj = iana_by_id.get(norm_obj.identifier)
                iana_op_ids = {op.identifier for op in iana_obj.operations} if iana_obj else set()
                missing_ops = [
                    op for op in norm_obj.operations
                    if op.identifier and op.identifier not in iana_op_ids
                ]
                if missing_ops:
                    print()
                    print(f"--- [OP MISSING IN IANA] object '{norm_obj.identifier}' ---")
                    for op in missing_ops:
                        print()
                        print(generate_iana_op_block(op))

            # Missing operation parameters → single row per parameter
            for norm_obj, obj_errors in op_errors:
                iana_obj = iana_by_id.get(norm_obj.identifier)
                iana_ops = {op.identifier: op for op in iana_obj.operations} if iana_obj else {}
                for nop in norm_obj.operations:
                    iop = iana_ops.get(nop.identifier)
                    if iop is None:
                        continue
                    iana_param_ids = {p.identifier for p in iop.params}
                    missing_params = [
                        p for p in nop.params
                        if p.identifier not in iana_param_ids
                    ]
                    if missing_params:
                        print()
                        print(f"--- [PARAM MISSING IN IANA] object '{norm_obj.identifier}', "
                              f"operation '{nop.identifier}' ---")
                        for param in missing_params:
                            print(generate_iana_param_row(param))

        return 1

    print("OK: all normative object and element definitions match their IANA entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
