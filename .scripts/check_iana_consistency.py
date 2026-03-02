#!/usr/bin/env python3
"""
Verify that all objects defined in the normative part of the document
(Component Objects, Process Objects, Data Objects) have matching
Object Identifier and Object Name in the IANA section.

Normative object-header format (at the start of each object's definition block):
  * Name: <Object Name>
  * Identifier: <identifier>

IANA format:
  Object: <identifier>
  Object Name: <Object Name>
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path


DRAFT_FILE = Path("./draft-kowalik-rpp-data-objects.md")

# Markdown section headings that contain normative object definitions.
# Objects are always introduced by "## <Something>" inside these sections.
NORMATIVE_TOPLEVEL_SECTIONS = [
    "# Component Objects",
    "# Process Objects",
    "# Domain Name Data Object",
    "# Contact Data Object",
    "# Host Data Object",
]

IANA_SECTION_MARKER = "# IANA Considerations"

# A "* Name:" bullet that starts an object definition block appears at
# indent level 0 (no leading spaces).  The data-element attribute bullets
# that look the same ("* Name:") appear indented or inside a nested list
# under "* Data Elements:".  We rely on this to distinguish them.
TOP_LEVEL_BULLET = re.compile(r"^\* Name:\s*(.+)$")
TOP_LEVEL_IDENT  = re.compile(r"^\* Identifier:\s*(\S+)")


@dataclass
class ObjectDef:
    name: str
    identifier: str
    source: str  # "normative" or "iana"
    line: int   # 1-based


def in_normative_section(current_h1: str | None) -> bool:
    """Return True when we are inside one of the sections that define objects."""
    if current_h1 is None:
        return False
    for marker in NORMATIVE_TOPLEVEL_SECTIONS:
        if current_h1.startswith(marker):
            return True
    return False


def parse_document(path: Path) -> tuple[list[ObjectDef], list[ObjectDef]]:
    text = path.read_text()
    lines = text.splitlines()

    normative_objects: list[ObjectDef] = []
    iana_objects: list[ObjectDef] = []

    # -------------------------------------------------------------------- #
    # Locate the IANA section                                              #
    # -------------------------------------------------------------------- #
    iana_start_line = None
    for i, line in enumerate(lines):
        if line.strip() == IANA_SECTION_MARKER:
            iana_start_line = i
            break

    if iana_start_line is None:
        print(f"ERROR: Could not find '{IANA_SECTION_MARKER}' section.", file=sys.stderr)
        sys.exit(1)

    # --------------------------------------------------------------------- #
    # Parse normative objects (before the IANA section)                     #
    #                                                                       #
    # A normative object block looks like:                                  #
    #   ## <Object Section Heading>          <- H2 under a known H1 sect.   #
    #                                                                       #
    #   * Name: <Object Name>                <- top-level bullet (no indent)#
    #   * Identifier: <identifier>           <- immediately follows         #
    #   * Description: ...                                                  #
    #   * Data Elements:                                                    #
    #     * ...  <- indented: data-element attributes, NOT object headers   #
    # --------------------------------------------------------------------- #
    current_h1 = None   # tracks the current H1 heading text
    i = 0
    while i < iana_start_line:
        line = lines[i]
        stripped = line.strip()

        # Track H1 section changes
        if re.match(r"^# [^#]", stripped):
            current_h1 = stripped

        if in_normative_section(current_h1):
            m_name = TOP_LEVEL_BULLET.match(line)   # no leading spaces allowed
            if m_name:
                obj_name = m_name.group(1).strip()
                # Look for "* Identifier:" within the next ~5 non-blank lines
                for j in range(i + 1, min(i + 6, iana_start_line)):
                    m_id = TOP_LEVEL_IDENT.match(lines[j])
                    if m_id:
                        normative_objects.append(
                            ObjectDef(
                                name=obj_name,
                                identifier=m_id.group(1).strip(),
                                source="normative",
                                line=i + 1,
                            )
                        )
                        break
                    # Stop looking if we hit a non-indented non-empty line
                    # that is not an Identifier bullet (it is a different bullet)
                    if lines[j].strip() and not lines[j].startswith(" ") and not lines[j].startswith("\t"):
                        if re.match(r"^\* ", lines[j]) and not TOP_LEVEL_IDENT.match(lines[j]):
                            break
        i += 1

    # -------------------------------------------------------------------- #
    # Parse IANA objects (from the IANA section onward)                    #
    #                                                                      #
    # Pattern:                                                             #
    #   Object: <identifier>                                               #
    #   <blank line(s)>                                                    #
    #   Object Name: <Object Name>                                         #
    # -------------------------------------------------------------------- #
    i = iana_start_line
    while i < len(lines):
        line = lines[i].rstrip()
        m_obj = re.match(r"^Object:\s*(\S+)\s*$", line)
        if m_obj:
            iana_id = m_obj.group(1).strip()
            # "Object Name:" MUST follow within a few lines
            for j in range(i + 1, min(i + 5, len(lines))):
                m_name = re.match(r"^Object Name:\s*(.+)$", lines[j].rstrip())
                if m_name:
                    iana_objects.append(
                        ObjectDef(
                            name=m_name.group(1).strip(),
                            identifier=iana_id,
                            source="iana",
                            line=i + 1,
                        )
                    )
                    break
        i += 1

    return normative_objects, iana_objects


def check_consistency(
    normative: list[ObjectDef], iana: list[ObjectDef]
) -> list[str]:
    errors: list[str] = []

    iana_by_id   = {o.identifier: o for o in iana}
    iana_by_name = {o.name: o for o in iana}
    normative_ids   = {o.identifier for o in normative}
    normative_names = {o.name: o for o in normative}

    # 1. Every normative object must appear in the IANA section with
    #    the same identifier AND the same name.
    for obj in normative:
        if obj.identifier not in iana_by_id:
            # Check whether the name matches an IANA entry with a different id
            if obj.name in iana_by_name:
                iana_obj = iana_by_name[obj.name]
                errors.append(
                    f"[ID MISMATCH] name='{obj.name}':\n"
                    f"  normative (line {obj.line}):   identifier='{obj.identifier}'\n"
                    f"  IANA     (line {iana_obj.line}):  identifier='{iana_obj.identifier}'"
                )
            else:
                errors.append(
                    f"[MISSING IN IANA] normative object at line {obj.line}: "
                    f"identifier='{obj.identifier}', name='{obj.name}' "
                    f"— no matching entry in IANA section."
                )
            continue

        iana_obj = iana_by_id[obj.identifier]
        if iana_obj.name != obj.name:
            errors.append(
                f"[NAME MISMATCH] identifier='{obj.identifier}':\n"
                f"  normative (line {obj.line}):   name='{obj.name}'\n"
                f"  IANA     (line {iana_obj.line}):  name='{iana_obj.name}'"
            )

    # 2. Every IANA object must have a corresponding normative definition.
    for obj in iana:
        if obj.identifier not in normative_ids:
            # Check whether the name matches a normative entry with a different id
            # (already reported as [ID MISMATCH] above — skip to avoid duplicate)
            if obj.name in normative_names:
                continue
            errors.append(
                f"[MISSING IN NORMATIVE] IANA object at line {obj.line}: "
                f"identifier='{obj.identifier}', name='{obj.name}' "
                f"— no matching normative definition found."
            )

    # 3. Duplicate identifiers within each section.
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


def main() -> int:
    if not DRAFT_FILE.exists():
        print(f"ERROR: file not found: {DRAFT_FILE}", file=sys.stderr)
        return 1

    normative, iana = parse_document(DRAFT_FILE)

    print(f"Normative objects found ({len(normative)}):")
    for o in normative:
        print(f"  line {o.line:4d}  identifier={o.identifier!r:30s}  name={o.name!r}")

    print(f"\nIANA objects found ({len(iana)}):")
    for o in iana:
        print(f"  line {o.line:4d}  identifier={o.identifier!r:30s}  name={o.name!r}")

    errors = check_consistency(normative, iana)

    print()
    if errors:
        print(f"CONSISTENCY ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print("OK: all normative object identifiers and names match their IANA entries.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
