%%%
title = "RESTful Provisioning Protocol (RPP) Data Objects"
abbrev = "RPP Data Objects"
area = "Internet"
workgroup = "Network Working Group"
submissiontype = "IETF"
keyword = [""]
TocDepth = 4
date = 2025-11-14

[seriesInfo]
name = "Internet-Draft"
value = "draft-kowalik-rpp-data-objects-02"
stream = "IETF"
status = "standard"

[[author]]
initials="P."
surname="Kowalik"
fullname="Pawel Kowalik"
abbrev = ""
organization = "DENIC"
  [author.address]
  email = "pawel.kowalik@denic.de"
  uri = "https://denic.de/"

[[author]]
initials="M."
surname="Wullink"
fullname="Maarten Wullink"
abbrev = ""
organization = "SIDN Labs"
  [author.address]
  email = "maarten.wullink@sidn.nl"
  uri = "https://sidn.nl/"

%%%

.# Abstract

This document defines data objects for the RESTful Provisioning Protocol (RPP) and sets up IANA RPP Data Object Registry to describe and catalogue them. Specifically, it details the logical structure, constraints, and protocol operations (including their inputs, outputs and business logic) for foundational resources: domain names, contacts, and hosts. In accordance with the RPP architecture [@!I-D.kowalik-rpp-architecture], these definitions focus entirely on the semantics, remaining independent of any specific data representation or media type (e.g., JSON or XML).

{mainmatter}

# Introduction
The RESTful Provisioning Protocol (RPP) defines a set of data objects used to represent and manage foundational registry resources, including domain names, contacts, and hosts. This initial list is not exhaustive; additional resource and component objects MAY be defined in future revisions or introduced via IANA registration to support new features and operational needs.

In accordance with the RPP architecture [@!I-D.kowalik-rpp-architecture], a core architectural principle is the clear distinction between the abstract data model and its concrete data representation. The data model defines the logical structure, relationships, and constraints of the objects, independent of formatting. The data representation defines how these abstract concepts are expressed in specific formats (e.g., JSON, XML, or YAML).

This document focuses on the data model of RPP objects and operations on them, including the data model of operation inputs, outputs as well as the necessary business logic of state transitions. This separation of concerns ensures the protocol maintains a stable semantic foundation that can be consistently implemented across different media types and easily adapted to new representation formats. For instance, the model defines a contact's name as a required string type, but it remains agnostic as to whether that string is ultimately encoded as a JSON property or an XML element.

## Conventions and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [@!RFC2119] [@!RFC8174] when, and only when, they appear in all capitals, as shown here.

The following terms related to the relationship between host objects and domain objects are used as defined in [@!RFC5732, section 1.1]:

* Subordinate host: A host name object that has a subordinate relationship to a superordinate domain name object. For example, host name "ns1.example.com" has a subordinate relationship to domain name "example.com".
* Superordinate domain: A domain name object to which a host name object is subordinate.
* Internal host: A host whose name belongs to the namespace of the repository in which the host is being used for delegation purposes.
* External host: A host whose name does not belong to the namespace of the repository in which the host is being used for delegation purposes.

# Resource Definition Principles

## Primitive Data Types

RPP data elements use strict typing, meaning that each element must conform exactly to its declared primitive data type, and type violations MUST be treated as errors by implementations. The exact specifications for these types, including allowed ranges, encoding, and formatting, are determined by the representation format used (e.g., JSON, XML, CBOR). New RPP non-primitive data types based on existing primitive data types MAY be defined to support additional features.

### String

A String is a sequence of Unicode characters. Usages MAY impose additional constraints on string values, such as maximum length or allowed character sets, based on specific data element definitions. An example of a string is `"host.example"`.

### Integer

An Integer is a whole number, positive or negative. Usages MAY impose additional constraints on integer values, such as minimum and maximum allowable values, based on specific data element definitions. An example of an integer is `42`.

### Boolean

A Boolean represents a logical true or false value. An example of a boolean is `true` or `false`, but it MAY be different depending on the native encoding of boolean values in the representation.

### Decimal

 Decimal is a number providing an exact, base-10 representation of fractional values within a defined precision. Usage of this type MUST impose additional constraints on decimal values, such as precision or range, based on specific data element definitions. An example of a decimal is 3.14159.

### Date

A Date is a full-date calendar date as described in [@!RFC3339], an example of a date is `2025-10-27`.

### Timestamp

Timestamp (Date and time attribute) values MUST be represented in Universal Coordinated Time (UTC) using the Gregorian calendar using date-time form as defined in [@!RFC3339]. In EPP Compatibility Profile upper case "T" and "Z" characters MUST be used. An example of a timestamp is `2025-10-27T09:42:51Z`.

### URL

A Uniform Resource Locator (URL) as defined in [@!RFC1738]. An example of a URL is `"https://host.example"`.

### Binary

Raw binary data, implementations MAY choose how to encode the binary data, for example as base64 or hexadecimal string. An example of binary data encoded as base64 is `"UlBQIFNheXMgSGk="`.

## Data Element Abstraction

Each data object is composed of logical data elements. A data element is a logical unit of information identified by a stable name, independent of its representation in any given media type. The definition for each element specifies its logical name, purpose, cardinality, data type, and constraints.
The data type of a data element may also be a reference to another data object, using the target object's stable name.

## Extensibility

The RPP data model is designed to be extensible. Extensions MAY introduce new data objects, add new data elements or associations to existing objects, and define new operations or extend the inputs and outputs of existing operations with additional transient data elements.

### Standardised and Private Extensions

RPP distinguishes between standardised and private extensions:

* Standardised extensions MUST be registered with IANA, as described in the IANA Considerations section of this document and in [@!I-D.ietf-rpp-architecture]. Registration ensures global uniqueness of extension identifiers and promotes interoperability across implementations.

* Private (non-standardised) extensions MAY be defined for use within specific implementations or organisations. Private extensions are not required to be registered with IANA, but MUST still use unique identifiers that are unlikely to conflict with standardised extensions or other private extensions. The use of reverse domain notation as a prefix (e.g., `org.example.rpp.myElement`) is RECOMMENDED for private extension identifiers to avoid naming collisions.

### Extension Points

The following aspects of the data model are extensible:

* New data objects: Additional resource or component objects MAY be defined by extensions and registered with IANA.
* New data elements: Extensions MAY add new data elements to existing data objects. Such elements follow the same Data Element Semantics as core data elements.
* New associations: Extensions MAY introduce new associations between existing or new objects.
* New operations: Extensions MAY define entirely new operations on existing or new data objects.
* Extended operation inputs and outputs: Extensions MAY add new transient data elements to the inputs or outputs of existing operations.

When an extension adds data elements or transient parameters to a core object or operation, these additions MUST NOT alter the semantics or constraints of existing core data elements.

## Data Element Semantics

The definition of each data element within an object consists of the following attributes:

* Name: A human-readable name for the data element.
* Identifier: A machine-readable, unique identifier for the element, using camelCase notation.
* Cardinality: Specifies the number of times an element may appear. The notation is as follows:
  * `1` for exactly one
  * `0-1` for zero or one
  * `0+` for zero or more
  * and `1+` for one or more
* Data Type: Defines the element's data structure, which can be a primitive type, a Common Data Type or a reference to another component object.
* Description: Explains the purpose of the data element and any other relevant information.
* Constraints: Provides specific validation rules or limitations on top of the data type itself, such as value ranges.
* Mutability: Defines the lifecycle of the data element's value. It MUST be one of the following:
  * create-only: The element's value is provided during the object's creation and cannot be modified thereafter.
  * read-only: The element's value is managed by the server. It cannot be set or modified directly by the client, though it may change as a result of server-side operations.
  * read-write: The element's value can be set and modified by the client.

## Operations

For each data object a set of possible operations is defined together with their respective input and output data.

### Authorisation

For each operation authorisation requirements and operation behaviour is specified.
Wherever "object authorisation" is mentioned, it means that an operation MAY accept or require additional authorisation data related to the object beyond default client-level authorisation, or that an operation MAY have different effect or response if such authorisation is provided.
Typically it would be a value related to or derived from Authorisation Information Object attached to the object.

### Uniform interface

For the typical set of Create, Read, Update and Delete operations the following set of input and output data model is specified on top of additional transient input data, unless an operation for the specific object tells otherwise.

#### Create

* Input: Object representation (create-only and read-write properties)
* Output: Object representation (read-write and read-only properties)

#### Read

* Input: Object identifier
* Output: Object representation (read-write and read-only properties)

The output representation MAY vary depending on the identity of the querying client, use of object authorisation information, and server policy towards unauthorized clients. If the querying client is the sponsoring client, all available information MUST be returned. If the querying client is not the sponsoring client but the client provides valid object authorisation information, all available information SHOULD be returned, however some optional elements MAY be reserved to the sponsoring client only. If the querying client is not the sponsoring client and the client does not provide valid object authorisation information, server policy determines which OPTIONAL elements are returned, if any, or whether the entire request is rejected.

#### Update

* Input: Object identifier, Object changes representation (read-write properties)
* Output: Object representation (read-write and read-only properties)

#### Delete

* Input: Object identifier
* Output: Object representation (read-write and read-only properties) or no representation

### Operations beyond uniform interface

For all other operations both input and output representation have to be fully specified.

### Transfer Operations

Transfer operations manage the change of sponsorship of a provisioned object from one client (the sponsoring client) to another (the gaining client). They are specified once in this section as the transfer model is common across all transferable resource objects. Individual object definitions reference this section and specify any object-specific extensions to the common pattern.

RPP supports two types of transfer:

* Pull Transfer: Initiated by the gaining client. The gaining client MUST provide valid authorisation information associated with the object to initiate the request.
* Push Transfer: Initiated by the sponsoring client, who designates a gaining client in the request.

The transfer process MAY be immediate or follow a multi-step workflow depending on server policy. If the server implements immediate transfers, the approve, reject, and cancel operations need not be supported; the server completes the transfer upon receipt of the request.

The server MAY implement local policies to prevent transfers from stalling and implement a form of automated transfer escalation, approval or cancellation when such a stalled process is recognised.

All transfer operations return the Transfer Data Object as output.

A> TODO: The server MUST notify the current sponsoring client of a pending transfer request. The notification mechanism is not defined in this document.

A> TODO: Transfer-specific error conditions (object not eligible for transfer, object pending transfer, object not pending transfer) are not defined in this document.

#### Transfer Request Operation

* Identifier: transferRequest

The Transfer Request operation initiates a transfer of an object.

* Input:
  * Object Identifier
  * Object authorisation information (REQUIRED only for pull transfers)
* Output: Transfer Data Object

The following transient data elements are common for all transfer requests:

* Transfer Direction
  * Identifier: transferDirection
  * Cardinality: 0-1
  * Data Type: String
  * Description: Indicates whether the transfer is a "pull" or "push" transfer. Per policy servers usually will support only one model.
  * Constraints: The value MUST be one of: "pull" or "push".

* Gaining Client ID
  * Identifier: gainingClientId
  * Cardinality: 0-1
  * Data Type: Client Identifier
  * Description: The identifier of the designated gaining client. This element is REQUIRED for push transfers and MUST NOT be provided for pull transfers.
  * Constraints: (None)

* Authorisation:
  * Pull transfer:
    * The requesting client (gaining client) MUST provide valid authorisation information associated with the object.
  * Push transfer:
    * Only the sponsoring client is authorised to initiate a push transfer.

#### Transfer Approve Operation

* Identifier: transferApprove

The Transfer Approve operation allows the appropriate client to accept a pending transfer request. For a pending pull transfer, only the sponsoring client is authorised to approve. For a pending push transfer, only the designated gaining client is authorised to approve.

* Input: Object Identifier
* Output: Transfer Data Object

* Authorisation:
  * Pull transfer: only the sponsoring client
  * Push transfer: only the designated gaining client
  * The server MUST reject any approval attempts not initiated by the authorised client.

#### Transfer Reject Operation

* Identifier: transferReject

The Transfer Reject operation allows the appropriate client to reject a pending transfer request. For a pending pull transfer, only the sponsoring client is authorised to reject. For a pending push transfer, only the designated gaining client is authorised to reject.

* Input: Object Identifier
* Output: Transfer Data Object

The following transient data elements are defined for this operation:

* Reason
  * Identifier: reason
  * Cardinality: 0-1
  * Data Type: String
  * Description: A human-readable text describing the rationale for rejecting the transfer request.
  * Constraints: In EPP Compatibility Profile this data element MUST NOT be used

* Authorisation:
  * Pull transfer: only the sponsoring client
  * Push transfer: only the designated gaining client
  * The server MUST reject any rejection attempts not initiated by the authorised client.

#### Transfer Cancel Operation

* Identifier: transferCancel

The Transfer Cancel operation allows the initiating client to cancel its own pending transfer request.

* Input: Object Identifier
* Output: Transfer Data Object

* Authorisation:
  * Only the initiating client (the client that originally requested the transfer) is authorised to cancel.
  * The server MUST reject any cancellation attempts not initiated by the initiating client.

#### Transfer Query Operation

* Identifier: transferQuery

The Transfer Query operation allows a client to determine the real-time status of a pending or recently completed transfer request.

* Input: Object Identifier
* Output: Transfer Data Object

* Authorisation:
  * This operation MUST be accessible to both the sponsoring client and the gaining client.
  * Server policy determines whether other clients may query transfer status and what information is returned.

### Restore Operations {#restore-ops}

Restore operations manage the recovery of an object that has entered the Redemption Grace Period (RGP). They are OPTIONAL and are only available when the RGP feature is supported by the server and MAY be supported only for a subset of Data Object types.

The RGP process MAY involve two distinct steps:

* Restore Request: (REQUIRED) Initiates the recovery of an object in the `redemptionPeriod` state, signalling to the registry the intent to restore. On success, the object transitions to `pendingRestore`.
* Restore Report: (OPTIONAL) Submits a report documenting the circumstances of the deletion and restoration, as required by registry policy. On success, the object is returned to its pre-deletion status and all RGP status labels are removed.

Whether a restore report is required after a restore request is a matter of server policy. If the server does not require a restore report, the object returns to its pre-deletion status immediately upon a successful restore request, bypassing the `pendingRestore` state.

The restore request MAY include the restore report inline to complete both steps atomically in a single operation.

All restore operations return the Restore Data Object as output.

#### Redemption Grace Period State Diagram

The following state diagram describes the object lifecycle when the Redemption Grace Period (RGP) feature is supported. It adapts the diagram from [@!RFC3915, section 2] to the RPP data model, using RPP status labels and operations instead of EPP command names.

In the diagram below, RPP status labels are shown in the `status` field of the object. Standard EPP-origin status labels (e.g., `ok`, `pendingDelete`) are used alongside the RGP-specific labels defined in this document. The `restore` operation replaces the EPP extended `<update>` command with `op=request` and `op=report` attributes.

```ascii
              |
              v                     (2)
+----------------------------+   <delete>   +-------------------------------+
| status: ok              (1)|------------->| status: pendingDelete      (3)|
|                            |              |         redemptionPeriod      |
+----------------------------+              +-------------------------------+
   ^   ^             restore, no report      | ^  |                |
   |   |             and report required  (4)| |  |        No (9)  |
   |   |               <restoreRequest>      | |  |       restore  |
   |   |                  +------------------+ |  |       restore  |
   |   |                  v                    |  |                v
   |   |  +------------------+                 |  | +-----------------------+
   |   |  | status:       (6)|                 |  | | status:           (10)|
   |   |  |   pendingDelete  |-----------------+  | |   pendingDelete       |
   |   |  |   pendingRestore |   report not (7)   | |   rgpPendingDelete    |
   |   |  +------------------+   received         | +-----------------------+
   |   |                (8) |                     |                |
   |   |    report received |                     |     purge (11) |
   |   |    <restoreReport> |      restore (5)    |                v
   |   +--------------------+      with report    | +-----------------------+
   |                               or not req.    | |      Purged       (12)|
   |                             <restoreRequest> | +-----------------------+
   +----------------------------------------------+
```

State descriptions:

1. The object is in normal operation (`ok` or other status allowing a delete operation).
2. A delete operation is received and processed.
3. RGP begins. The object enters `pendingDelete` + `redemptionPeriod` state. The object remains here until a restore operation is requested or the redemption period elapses.
4. A restore operation is requested. The registry accepts the request. Go to step 8 if the redemption period elapses before a restore is received (4a). 
5. If the server does not require a restore report, the object returns to its pre-deletion status (1) immediately upon a successful `restoreRequest` operation. If the server requires a report but the client includes it inline in the `restoreRequest`, the server processes both atomically and the object transitions directly from `redemptionPeriod` to its pre-deletion status (1), bypassing the `pendingRestore` state.
6. The object enters `pendingDelete` + `pendingRestore` state. The registry awaits a restore report from the sponsoring client.
7. If no restore report is received within the registry-defined time, the object returns to `redemptionPeriod` state (step 3).
8. If a restore report is received and accepted, the object returns to its pre-deletion status and all RGP status labels are removed.
9. The redemption period elapses without a restore request being received.
10. The object enters `pendingDelete` + `rgpPendingDelete` state and awaits final purge processing.
11. The pending delete period elapses and the object is purged.
12. The object is purged and available for re-registration.

#### Restore Request Operation

* Identifier: restoreRequest

The Restore Request operation initiates the recovery of an object in the `redemptionPeriod` state. The server MUST reject this operation if the object is not in the `redemptionPeriod` state.

* Input: Object Identifier
* Output: Restore Data Object

* Authorisation:
  * Only the sponsoring client is authorised to perform this operation.

The following transient data elements are defined for this operation:

* Restore Report
  * Identifier: restoreReport
  * Cardinality: 0-1
  * Data Type: Restore Report Object
  * Description: An OPTIONAL inline restore report. If provided, the server processes the request and the report atomically. If the server does not require a restore report, this element MUST NOT be present and the restore is completed immediately. If the server requires a report and this element is absent, the object transitions to `pendingRestore` state awaiting a subsequent Restore Report operation.
  * Constraints:
    * MUST NOT be provided if the server does not require a restore report.
    * In EPP Compatibility Profile, corresponds to `op="request"` (without report) or a combined `op="request"` followed immediately by `op="report"` as defined in [@!RFC3915].

#### Restore Report Operation

* Identifier: restoreReport

This operation is OPTIONAL, only for the servers which support or require submission of restore report.

The Restore Report operation submits the restore report required by the RGP process for an object in the `pendingRestore` state. A report MAY be submitted more than once if corrections are required. The server MUST reject this operation if the object is not in the `pendingRestore` state.

* Input: Object Identifier, Restore Report Object
* Output: Restore Data Object

* Authorisation:
  * Only the sponsoring client is authorised to perform this operation.

The following transient data elements are defined for this operation:

* Restore Report
  * Identifier: restoreReport
  * Cardinality: 1
  * Data Type: Restore Report Object
  * Description: The restore report to be submitted as part of the RGP process.
  * Constraints:
    * In EPP Compatibility Profile, corresponds to `op="report"` as defined in [@!RFC3915].

#### Restore Query Operation

* Identifier: restoreQuery

The Restore Query operation allows the sponsoring client to retrieve the current state of the RGP process for an object.

* Input: Object Identifier
* Output: Restore Data Object

* Authorisation:
  * Only the sponsoring client is authorised to perform this operation.

In EPP Compatibility Profile this operation is not supported.

## EPP Compatibility Profile

RPP is designed to coexist with the Extensible Provisioning Protocol (EPP), often operating in parallel against a common backend provisioning system. While RPP is not inherently constrained by all of EPP's requirements, a specific set of rules is necessary to ensure seamless interoperability in such mixed environments.

To address this, this document defines an "EPP Compatibility Profile". This profile specifies a set of additional constraints on RPP data objects and operations that a server MUST adhere to when supporting both RPP and EPP concurrently.

Throughout this document, all constraints that are part of this profile are explicitly marked with a reference to "EPP Compatibility Profile". Implementers of systems in a mixed EPP/RPP environment MUST follow these specific constraints in addition to the base RPP requirements.

# Common Data Types

This section defines new shared data types and structures that are re-used across multiple data object definitions and are based on the existing Primitive Data Types.

## Identifier

Identifiers are character strings with a specified minimum length, a specified maximum length, and a specified format outlined in [@!RFC5730, section 2.8]. Identifiers for certain object types MAY have additional constraints imposed either by server policy, object specific specifications or both.

## Client Identifier

Client identifiers are character strings with a specified minimum length, a specified maximum length, and a specified format. Contact identifiers use the "clIDType" client identifier syntax described in [@!RFC5730].

A> TBC: do we need this or is it a relation with an entity/RFC8543 organisation? If registrars modeled are as first class objects (organisations), then clID is nothing else but a reference to this organisation, so maybe no need to define syntax separately on identifier level (or in other words it would be defined on this object). R8.1 in the form of -02 RPP requirements includes RFC8543. 

## Phone Number

Telephone number syntax is derived from structures defined in [@!ITU.E164.2005].  Telephone numbers described in this specification are character strings that MUST begin with a plus sign ("+", ASCII value 0x002B), followed by a country code defined in [@!ITU.E164.2005], followed by a dot (".", ASCII value 0x002E), followed by a sequence of digits representing the telephone number.  An optional "x" (ASCII value 0x0078) separator with additional digits representing extension information can be appended to the end of the value.

# Associations

RPP allows for different types of associations (relationship) between the objects. The association may be added between 2 objects with own indpendent lifecycle (UML aggregation) or in the relation when one object's existance and lifecycle is bound to the other parent/owner object (UML composition).
In both cases, especially if the relation allows for cardinality higher than one on either side, the association may be assigned additional attributes, not being part of an object on either side of relation. In many cases such relation would be attributed with a single text string label, describing a role or a type of relation. Depending on the context this value might be unique, which allows using such label as a key in a dictionary.

The following generic Association Types are defined for RPP:

## Aggregation

Notation: Aggregation[Type]

A relation between two independent objects.

If the cardinality of target object is more than 1, this represents an ordered array. 
It MUST assured that the same unchanged data is always inserted in the same order in order to allow stable reference by position to data elements. In case of data insertions, deletions or updates the remaining of the data SHALL preserve its order.

Example aggregation having cardinality 1:

```ascii
+-------------------+
|   (root parent)   |
|-------------------|
| foo:              |
|   |         +----------+
|   +-------- | [Object] |
|             |    ...   |
|             +----------+
+-------------------+
```

Example aggregation having cardinality >1:

```ascii
+-------------------+
|   (root parent)   |
|-------------------|
| foo:              |
|   +-----[0] +----------+
|   |         | [Object] |
|   |         |    ...   |
|   |         +----------+
|   +-----[1] +----------+
|             | [Object] |
|             |    ...   |
|             +----------+
|         ...       |
+-------------------+
```

## Composition

Notation: Composition[Type] or Type

A relation between an independent parent object and 1 or more dependent child object(s).

If the cardinality of target object is more than 1, this represents an ordered array. 
It MUST assured that the same unchanged data is always inserted in the same order  in order to allow stable reference by position to data elements. In case of data insertions, deletions or updates the remaining of the data SHALL preserve its order.

Example composition having cardinality 1:

```ascii
+-------------------+
|      (root)       |
|-------------------|
| foo:              |
|   |  +-------+    |
|   +--| ...   |    |
|      +-------+    |
+-------------------+
```

Example composition having cardinality >1:

```ascii
+-------------------+
|      (root)       |
|-------------------|
| foo:              |
|   +-[0] +-------+ |
|   |     | ...   | |
|   |     +-------+ |
|   +-[1] +-------+ |
|   |     | ...   | |
|   |     +-------+ |
|   ...             |
+-------------------+
```

## Labelled Aggregation

Notation: LabelledAggregation[Type]

A relation between two independent object with single text string attribute. Multiple associations with the same label are allowed and represent an unordered array.

A type defining such association MUST define Label Description with semantics of the label and Label Constraints with constraints related to the label.

Example labelled aggregation:

```ascii
+--------------------------------+
|             (root)             |
|--------------------------------|
| foo:                           |
|   |                            |
|   +---("label_A")--->  +----------+
|   |                    | [Object] |
|   |                    |   ...    |
|   |                    +----------+
|   +---("label_B")--->  +----------+
|   |                    | [Object] |
|   |                    |   ...    |
|   |                    +----------+
|   +---("label_A")--->  +----------+
|   |  (labels repeat)   | [Object] |
|   |                    |   ...    |
|   |                    +----------+
|   ...                          |
+--------------------------------+

```

## Dictionary Aggregation

Notation: DictionaryAggregation[Type]

A relation between two independent object with single text string attribute. Association labels MUST be unique allowing it to be used as dictionary key.

A type defining such association MUST define Label Description with semantics of the label and Label Constraints with constraints related to the label.

Example Dictionary Aggregation:

```ascii
+--------------------------+
|         (root)           |
|--------------------------|
| foo:                     |
|   "key1" ->       +-----------+
|                   | [Object]  |
|                   |   ...     |
|                   +-----------+
|   "key2" ->       +-----------+
|                   | [Object]  |
|                   |   ...     |
|                   +-----------+
|     ...                  |
+--------------------------+
```

## Labelled Composition

Notation: LabelledComposition[Type]

A relation between an independent parent object and a dependent child object with single text string attribute. Multiple associations with the same label are allowed.

A type defining such association MUST define Label Description with semantics of the label and Label Constraints with constraints related to the label.

Example Labelled Composition:

```ascii
+-------------------------------------+
|        (root parent)                |
|-------------------------------------|
| foo:                                |
|   |                                 |
|   +---("label_A")--->  +----------+ |
|   |                    | [Child]  | |
|   |                    |   ...    | |
|   |                    +----------+ |
|   +---("label_B")--->  +----------+ |
|   |                    | [Child]  | |
|   |                    |   ...    | |
|   |                    +----------+ |
|   +---("label_A")--->  +----------+ |
|   |  (labels repeat)   | [Child]  | |
|   |                    |   ...    | |
|   |                    +----------+ |
|   ...                               |
+-------------------------------------+
```

## Dictionary Composition

Notation: DictionaryComposition[Type]

A relation between an independent parent object and a dependent child object with single text string attribute. Only single association with the same label is allowed allowing it to be used as dictionary key.

A type defining such association MUST define Label Description with semantics of the label and Label Constraints with constraints related to the label.

Example Dictionary Composition:
```ascii
+--------------------------+
|         (root)           |
|--------------------------|
| foo:                     |
|   "key1" -> +---------+  |
|             | [Child] |  |
|             |   ...   |  |
|             +---------+  |
|   "key2" -> +---------+  |
|             | [Child] |  |
|             |   ...   |  |
|             +---------+  |
|     ...                  |
+--------------------------+
```


# Component Objects

This section defines common objects that are re-used in the definitions of top-level data objects.
Component objects carry only data but do not define any operations.

## Period Object

* Name: Period Object
* Description: Represents a duration of time.
* Data Elements:
  * Value
    * Identifier: value
    * Cardinality: 1
    * Mutability: read-write
    * Data Type: Integer
    * Description: The numeric value of the period.
    * Constraints: The value MUST be from 1 to 99, inclusive.
  * Unit
    * Identifier: unit
    * Cardinality: 1
    * Mutability: read-write
    * Data Type: String
    * Description: The unit of the period.
    * Constraints: The value MUST be one of: "y" (years) or "m" (months).

## Provisioning Metadata Object

* Name: Provisioning Metadata Object
* Identifier: provisioningMetadata
* Description: Contains standard metadata about the lifecycle and ownership of a provisioned object. This metadata is common across all resource objects in the registry system.
* Data Elements:
  * Repository ID
    * Identifier: repositoryId
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Identifier
    * Description: A server-assigned unique identifier for the object.
    * Constraints: In EPP Compatibility Profile this data element MUST be provided.
  * Sponsoring Client ID
    * Identifier: sponsoringClientId
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: Client Identifier
    * Description: The identifier of the client that is the current sponsor of the object.
    * Constraints: (None)
  * Creating Client ID
    * Identifier: creatingClientId
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Client Identifier
    * Description: The identifier of the client that created the object.
    * Constraints: (None)
  * Creation Date
    * Identifier: creationDate
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: The date and time of object creation.
    * Constraints: The value is set by the server and cannot be specified by the client.
  * Updating Client ID
    * Identifier: updatingClientId
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Client Identifier
    * Description: The identifier of the client that last updated the object.
    * Constraints: This element MUST NOT be present if the object has never been modified.
  * Update Date
    * Identifier: updateDate
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: The date and time of the most recent object modification.
    * Constraints: This element MUST NOT be present if the object has never been modified.
  * Transfer Date
    * Identifier: transferDate
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: The date and time of the most recent successful object transfer.
    * Constraints: This element MUST NOT be provided if the object has never been transferred.

## Status Object

* Name: Status Object
* Description: Represents one of the status values associated with a provisioning object
* Data Elements:
  * Label
    * Identifier: label
    * Cardinality: 1
    * Mutability: create-only
    * Data Type: String
    * Description: machine-readible enum label of a status
    * Constraints:      
      * Exact list of allowed status labels depends on the provisioning object type. This enumeration can be expanded by extensions.
      * The status labels MUST use camel case notation and use only ASCII alphabetic characters.
      * Statuses MAY be of three categories:
        1. those explicitly set by a server. Those MUST have "server" prefix
        2. those explicitly set by a client. Those MUST have "client" prefix
        3. those indirectly controlled by provisioning object lifecycle or business logic. Those MUST NOT use either "client" or "server" prefix. They MAY use another prefix or no prefix at all
      * The following additional status labels are defined for use with the Redemption Grace Period (RGP) feature. When the RGP feature is supported, these labels MAY be specified:
        * `addPeriod`: The object is within the add grace period following initial registration. If the object is deleted during this period, the registry MAY provide a credit to the sponsoring client.
        * `autoRenewPeriod`: The object is within the auto-renew grace period following automatic renewal by the registry. If the object is deleted during this period, the registry MAY provide a credit to the sponsoring client.
        * `renewPeriod`: The object is within the renew grace period following an explicit renewal. If the object is deleted during this period, the registry MAY provide a credit to the sponsoring client.
        * `transferPeriod`: The object is within the transfer grace period following a successful transfer. If the object is deleted by the new sponsoring client during this period, the registry MAY provide a credit.
        * `redemptionPeriod`: A delete operation has been received and processed for the object, but the object has not yet been purged. A restore operation MAY be requested to abort the deletion. This status value MUST only appear alongside the standard `pendingDelete` status.
        * `pendingRestore`: A restore request has been accepted and the registry is waiting for a restore report from the sponsoring client. This status value MUST only appear alongside the standard `pendingDelete` status.
        * `rgpPendingDelete`: The redemption period has elapsed without a successful restore. The object has entered the purge processing state. This status value MUST only appear alongside the standard `pendingDelete` status. This label is used to distinguish the RGP-specific pending-delete sub-state from the broader EPP `pendingDelete` status.

A> TODO: find a better home for this list (own section + IANA registry). Add standard domain statuses here as well (and solve the issue of statuses not applicable to other object types like client/serverHold).
      
  * Reason
    * Indentifier: reason
    * Cardinality: 0-1
    * Mutability: create-only
    * Data Type: String
    * Description: a human-readable text that describes the rationale for the status applied to the object.
    * Constraints: None
  * Due
    * Identifier: due
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: Timestamp
    * Description: a timestamp, when this status is going to be removed automatically, or changed to other status. This field can be used to expresse lifecycle related information.
    * Constraints: servers MAY restrict possibility to set or update this value by the client.

A> TBD: Idea - model status object as Labelled Composition using "Label"? Con: Generic Constraints for Label will be repeated.

## DNS Resource Record

* Name: DNS Resource Record
* Description: Represents a DNS Entry
* Data Elements:
  * Label
    * Identifier: hostNamelabel
    * Cardinality: 1
    * Mutability: read-write
    * Data Type: String.
    * Description: DNS entry label.
    * Constraints: 
      * The value MUST be a syntactically valid DNS host name in Zone file string representation. 
      * Absolute FQDNs and relative host names are allowed.
  * Type
    * Identifier: type
    * Cardinality: 1
    * Mutability: read-write
    * Data Type: String.
    * Description: DNS entry type.
    * Constraints: 
      * Each value MUST be a valid string representation of resource record type as defined in [@!RFC1035]. 
      * Allowed values MAY be constrained by server policies. For domain provisioning typically the Type would be constrained to the allowed parent side entries.
  * Data
    * Identifier: data
    * Cardinality: 1
    * Mutability: read-write
    * Data Type: String.
    * Description: DNS entry value.
    * Constraints: Each value MUST be a syntactically valid resource record data for a Type in zone file string representation.
  * TTL
    * Identifier: ttl
    * Cardinality: 1
    * Mutability: read-write
    * Data Type: Number.
    * Description: TTL value of a resource record as defined in [@!RFC1035].
    * Constraints: The allowed value range MAY be constrained by server policy.

## Authorisation Information Object

* Name: Authorisation Information
* Description: Contains information used to authorise operations on a data object. It may hold different kind of authorisation information. 
* Data Elements:
  * Method
    * Identifier: method
    * Cardinality: 1
    * Mutability: create-only
    * Data Type: String
    * Description: The identifier of the RPP authorisation method.
    * Constraints:
      * The value MUST be one of the values registered at IANA as defined in [I-D.draft-wullink-rpp-core].
      * In EPP Compatibility Profile this value MUST be set to `authinfo` if standard password base authorisation is used
  * Authorisation Information
    * Identifier: authdata
    * Cardinality: 1
    * Mutability: create-only
    * Data Type: String
    * Description: The value of the authorisation information. It might be as simple as password string, but also more complex values like public key certificates or tokens encoded as string are possible.
    * Constraints: 
      * Authorisation Information object is immutable. If the information changes (for example password is updated) a new instance MUST be created.
      * Depending on the method and server policy Authorisation Information MAY not be available for read or any other operation responding with this data element.

## Postal Address Object

* Name: Postal Address Object
* Description: Contains the components of a postal address.
* Data Elements:
  * Street
    * Identifier: street
    * Cardinality: 0+
    * Mutability: read-write
    * Data Type: String
    * Description: The contact's street address.
    * Constraints: Implementations MAY limit the maximum length of entries or character set.
  * City
    * Identifier: city
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: The contact's city.
    * Constraints:
      * Implementations MAY limit the maximum length of entries or character set.
      * In EPP Compatibility Profile this data element MUST be provided.
  * State/Province
    * Identifier: sp
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: The contact's state or province.
    * Constraints: Implementations MAY limit the maximum length of entries or character set.
  * Postal Code
    * Identifier: pc
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: The contact's postal code.
    * Constraints:
      * Implementation MAY limit the maximum length of entries or character set.
      * The limitations MAY differ depending on Country Code (`cc`) data element.
  * Country Code
    * Identifier: cc
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: The contact's country code.
    * Constraints: 
      * The value MUST be a two-character identifier from [@!ISO3166-1].
      * In EPP Compatibility Profile this data element MUST be provided.

## Postal Info Object

* Name: Postal Info Object
* Description: Contains postal-address information in either internationalised or localised forms.
* Data Elements:

A> TBC: Contact Type is not localised (shall be the same for PERSON and ORG). Moving it level up would however detach it from related/dependant fields Name/Organisation

  * Contact Type
    * Identifier: type 
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: Specifies whether the contact is and individual or an organisation.
    * Constraints: The value MUST be one of: "PERSON" (individual) or "ORG" (organisation).
  * Name
    * Identifier: name
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: The name of the individual or role.
    * Constraints:
      * Implementations MAY limit the maximum length of entries or character set.
      * In EPP Compatibility Profile this data element MUST be provided.
      * The implementations MAY require this field if Contact Type (`type`) is set to "PERSON".
  * Organisation
    * Identifier: org
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: The name of the organisation.
    * Constraints:
      * Implementations MAY limit the maximum length of entries or character set.
      * The implementations MAY require this field if Contact Type (`type`) is set to "ORG".
  * Address
    * Identifier: addr
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: Postal Address Object
    * Description: The detailed postal address.
    * Constraints: In EPP Compatibility Profile this data element MUST be provided.

## Transfer Data Object

* Name: Transfer Data Object
* Identifier: transferData
* Description: Represents the state of a transfer request for a provisioned object. This object is returned as the output of transfer operations (request, approve, reject, cancel, query) for any transferable resource object.
* Data Elements:
  * Transfer Status
    * Identifier: transferStatus
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: String
    * Description: The state of the most recent transfer request.
    * Constraints: The value MUST be one of: "pending", "clientApproved", "clientCancelled", "clientRejected", "serverApproved", "serverCancelled".
  * Transfer Direction
    * Identifier: transferDirection
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: String
    * Description: Indicates the direction of the transfer.
    * Constraints: The value MUST be one of: "pull" (initiated by the gaining client) or "push" (initiated by the sponsoring client).
  * Requesting Client ID
    * Identifier: requestingClientId
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: Client Identifier
    * Description: The identifier of the client that initiated the transfer request.
    * Constraints: (None)
  * Request Date
    * Identifier: requestDate
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: The date and time that the transfer was requested.
    * Constraints: (None)
  * Acting Client ID
    * Identifier: actingClientId
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: Client Identifier
    * Description: For a pending pull transfer, the identifier of the sponsoring client that SHOULD act upon the request. For a pending push transfer, the identifier of the designated gaining client that SHOULD act upon the request. For all other statuses, the identifier of the client that took the indicated action.
    * Constraints: (None)
  * Action Date
    * Identifier: actionDate
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: For a pending request, the date and time by which a response is required before an automated response action SHOULD be taken by the server. For all other statuses, the date and time when the request was completed.
    * Constraints: (None)

## Disclose Object

A> TODO: Model Disclose in universal (extendible) way

* Name: Disclose
* Identifier: disclose
* Description: TBD

## Restore Data Object

* Name: Restore Data Object
* Identifier: restoreData
* Description: Represents the current state of a restore request for an object that has entered the Redemption Grace Period (RGP).
* Data Elements:
  * Restore Status
    * Identifier: restoreStatus
    * Cardinality: 1
    * Mutability: read-only
    * Data Type: String
    * Description: The current state of the restore process.
    * Constraints: The value MUST be one of: `"pendingRestore"`, `"restored"`, `"rgpPendingDelete"`
  * Request Date
    * Identifier: requestDate
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: The date and time when the restore request was submitted.
    * Constraints: MUST NOT be present if no restore request has been submitted yet.
  * Report Date
    * Identifier: reportDate
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: The date and time when the most recent restore report was accepted by the server.
    * Constraints: MUST NOT be present if no restore report has been accepted yet.
  * Report Due Date
    * Identifier: reportDueDate
    * Cardinality: 0-1
    * Mutability: read-only
    * Data Type: Timestamp
    * Description: The date and time by which a restore report must be submitted before the object reverts to `redemptionPeriod` state. Only present when the object is in `pendingRestore` state.
    * Constraints: MUST NOT be present when `restoreStatus` is not `"pendingRestore"`.

## Restore Report Object

* Name: Restore Report Object
* Identifier: restoreReport
* Description: Contains the redemption grace period restore report submitted by the sponsoring client as required by the RGP process ([@!RFC3915]). A restore report documents the state of the object before and after deletion, provides the reason for restoration, and includes mandatory client statements. This object is OPTIONAL and is only required when the RGP feature is supported and a restore report is being submitted.
* Data Elements:
  * Pre-Delete Data
    * Identifier: preData
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: A copy of the registration data that existed for the object prior to the object being deleted.
    * Constraints: None.
  * Post-Restore Data
    * Identifier: postData
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: A copy of the registration data that exists for the object at the time the restore report is submitted.
    * Constraints: None.
  * Delete Time
    * Identifier: deleteTime
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: Timestamp
    * Description: The date and time when the object delete request was sent to the server.
    * Constraints: None.
  * Restore Time
    * Identifier: restoreTime
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: Timestamp
    * Description: The date and time when the original restore request operation was sent to the server.
    * Constraints:
      * This element MAY be omitted when the restore report is submitted inline within the restore request in a single-step process.
      * In EPP Compatibility Profile this element MUST be present as defined in [@!RFC3915].
  * Restore Reason
    * Identifier: restoreReason
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: A brief explanation of the reason for restoring the object.
    * Constraints: None.
  * Statements
    * Identifier: statements
    * Cardinality: 0+
    * Mutability: read-write
    * Data Type: String
    * Description: Client statements required by the RGP process.
    * Constraints: At least one and at most two statements MUST be provided. In EPP Compatibility Profile exactly two statements MUST be present as defined in [@!RFC3915].
  * Other
    * Identifier: other
    * Cardinality: 0-1
    * Mutability: read-write
    * Data Type: String
    * Description: Any additional information needed to support the statements provided by the client.
    * Constraints: None.

# Domain Name Data Object

## Object Description

* Name: Domain Name Data Object
* Identifier: domainName
* Description: A Domain Name data object represents a domain name and contains the data required for its provisioning and management in the registry.

## Data Elements

The following data elements are defined for the Domain Name Data Object.

* Name
  * Identifier: name
  * Cardinality: 1
  * Mutability: create-only
  * Data Type: String
  * Description: The fully qualified name of the domain object.
  * Constraints:
    * The value MUST be a fully qualified domain name that conforms to the syntax described in [@!RFC1035].
    * A server MAY restrict allowable domain names to a particular top-level domain, second-level domain, or other domain for which the server is authoritative.
    * The trailing dot required when these names are stored in a DNS zone is implicit and MUST NOT be provided when exchanging host and domain names.

* Provisioning Metadata
  * Identifier: provisioningMetadata
  * Cardinality: 1
  * Mutability: read-only
  * Data Type: Provisioning Metadata Object
  * Description: Standard metadata about the object's lifecycle and ownership.
  * Constraints: (None)

* Status
  * Identifier: status
  * Cardinality: 0+
  * Mutability: read-only
  * Data Type:  Status Object
  * Description: The current status descriptors associated with the domain.
  * Constraints:
    * Possible combinations of Status Object Labels is specified in [@!RFC5731, section 2.3].

A> TBC: IANA registry for statuses?

* Registrant
  * Identifier: registrant
  * Cardinality: 0-1
  * Mutability: read-write
  * Data Type: Contact Object.
  * Description: The contact object associated with the domain as the registrant.
  * Constraints:
    * The relation MUST correspond to a valid Contact Data Object known to the server.
    * Servers MAY restrict association of a Contact Object of a different sponsoring client.

A> TBC: leave registrant here or move it to contacts with a type?

* Contacts
  * Identifier: contacts
  * Cardinality: 0+
  * Mutability: read-write
  * Data Type: LabelledAggregation[Contact Object]
    * Label Description: The role of the associated contact.
    * Label Constraints:
      * List of supported roles is defined by server policy
      * In the EPP Compatibility Profile, the value MUST be one of: "admin", "billing", or "tech"
  * Description: A collection of other contact objects associated with the domain object.
  * Constraints: 
    * Maximum number of associated contacts (per role) MAY be restricted by server policy

A> TBC: IANA registry for contact role label? 

* Nameservers
  * Identifier: nameservers
  * Cardinality: 0+
  * Mutability: read-write
  * Data Type: Aggregation[Host Data Object]
  * Description: A collection of nameservers associated with the domain.
  * Constraints: (None)

* DNS
  * Identifier: dns
  * Cardinality: 0+
  * Mutability: read-write
  * Data Type: Composition[DNS Resource Record]
  * Description: A collection of DNS entries related to the domain name.
  * Constraints:
    * The Type of the entries MAY be constrained by the server policy. Typically the values would be limited to allowed parent side resource record types.
    * In EPP Compatibility Profide with DNSSEC Extension allowed values MUST be DS and DNSKEY.
    * The labels of DNS entries MUST be subordinate to the domain name and MUST NOT be below zone cut in case of present delegation. 

* Subordinate Hosts
  * Identifier: subordinateHosts
  * Cardinality: 0+
  * Mutability: read-only
  * Data Type: Aggregation[Host Data Object]
  * Description: A collection of subordinate host objects that exist under this domain.
  * Constraints: (None)

* Expiry Date
  * Identifier: expiryDate
  * Cardinality: 0-1
  * Mutability: read-only
  * Data Type: Timestamp.
  * Description: The date and time identifying the end of the domain object's registration period.
  * Constraints: The value is set by the server and cannot be specified by the client.

* Authorisation Information
  * Identifier: authInfo
  * Cardinality: 0-1
  * Mutability: read-write
  * Data Type: Authorisation Information Object
  * Description: Authorisation information associated with the domain object.
  * Constraints: (None)

## Operations

### Create Operation

* Identifier: create

The Create operation allows a client to provision a new Domain Name resource. The operation accepts as input all create-only and read-write data elements defined for the Domain Name Data Object.

* Authorisation:
  * Generally each client is authorised to create new domain objects becoming a sponsoring client. This can be however constrained by the server policy in many ways, i.e. by applying rate limiting, billing related constraints or compliance locks.

In addition, the following transient data element is defined for this operation:

* Registration Period
  * Identifier: period
  * Cardinality: 0-1
  * Data Type: Period Object.
  * Description: The initial registration period for the domain name. This value is used by the server to calculate the initial `expiryDate` of the object. This element is not persisted as part of the object's state. 

### Read Operation

* Identifier: read

The Read operation allows a client to retrieve the data elements of a
Domain Name resource. The server's response MAY vary depending on
client authorisation and server policy.

* Authorisation:
  * Sponsoring client:
    * Full object representation
  * Other client:
    * Without object authorisation:
      * Limited (non-confidential) object representation or operation denied
    * With object authorisation:
      * Full object representation, however some properties only authorised to the sponsoring client MAY be redacted according to server policy

The following transient data elements are defined for this operation:

* Hosts Filter
  * Identifier: hostsFilter
  * Cardinality: 0-1
  * Data Type: String
  * Description: Controls which host information is returned with
the object.
  * Constraints: The value MUST be one of "all", "del"
(delegated), "sub" (subordinate), or "none". The default value
is "all".

### Delete Operation

* Identifier: delete

The Delete operation allows a client to remove an existing Domain Name resource. The operation targets a specific data object identified by its name.

* Authorisation:
  * Only sponsoring client is authorised to perform this operation

The server SHOULD reject a delete request if subordinate host objects are associated with the domain name.

The error response SHOULD indicate the related subordinate host objects.

### Renew Operation

* Identifier: renew

The Renew operation allows a client to extend the validity period of an existing Domain Name resource. The operation targets a specific data object identified by its name.


* Authorisation:
  * Only sponsoring client is authorised to perform this operation
* Input: Domain Name
* Output: Full object representation (read-write and read-only properties), or a minimum representation of properties affected by the operation (Expiry Date).

The following transient data elements are defined for this operation:

* Current Expiry Date
  * Identifier: currentExpiryDate
  * Cardinality: 1
  * Data Type: Timestamp
  * Description: The current expiry date of the domain name. The server MUST validate this against the object's current `expiryDate` to prevent unintended duplicate renewals.

* Renewal Period
  * Identifier: renewalPeriod
  * Cardinality: 0-1
  * Data Type: Period Object
  * Description: The duration to be added to the object's registration period. This value is used by the server to calculate the new `expiryDate`. The default value MAY be defined by server policy. The number of units available MAY be subject to limits imposed by the server.

### Transfer Operations

The Domain Name Data Object supports the common transfer operations defined in the [Transfer Operations] section. The transfer of a domain name changes the sponsoring client of the domain object.

Transfer of a domain object MUST implicitly transfer all host objects that are subordinate to the domain object. For example, if domain object "example.com" is transferred and host object "ns1.example.com" exists, the host object MUST be transferred as part of the "example.com" transfer process.

In addition to the common transfer data elements, the following object-specific transient data elements are defined for the Transfer Request operation:

* Transfer Period
  * Identifier: transferPeriod
  * Cardinality: 0-1
  * Data Type: Period Object
  * Description: The number of units to be added to the registration period of the domain object upon successful completion of the transfer. The number of units available MAY be subject to limits imposed by the server.
  * Constraints: This element is only applicable to the Transfer Request operation and MUST be ignored for other transfer operations.

In addition to the common Transfer Data Object elements, the following object-specific data element is included in the output of domain transfer operations:

* Expiry Date
  * Identifier: expiryDate
  * Cardinality: 0-1
  * Data Type: Timestamp
  * Description: The end of the domain object's registration period if the transfer caused or causes a change in the validity period.

Subordinate host objects MUST be transferred implicitly when the domain object is transferred.

### Restore Operations

The Domain Name Data Object supports the restore operations defined in the  section. These operations are OPTIONAL and are only available when the RGP feature is supported.

No domain-specific transient data elements extend the common restore operations beyond those defined in the (#restore-ops).

# Contact Data Object

## Object Description

* Name: Contact Data Object
* Identifier: contact
* Description: A Contact Data Object represents the social information for an individual or organisation associated with other objects.

## Data Elements

The following data elements are defined for the Domain Name Data Object.

* Handle ID
  * Identifier: id
  * Cardinality: 1
  * Mutability: create-only
  * Data Type: Identifier.
  * Description: External unique identifier of the contact object.
  * Constraints:
    * This value MUST be supported to be provided by the client.
    * Servers MAY support server-side generation of this value.

* Provisioning Metadata
  * Identifier: provisioningMetadata
  * Cardinality: 1
  * Mutability: read-only
  * Data Type: Provisioning Metadata Object
  * Description: Standard metadata about the object's lifecycle and ownership.
  * Constraints: (None)

* Status
  * Identifier: status
  * Cardinality: 0+
  * Mutability: read-only
  * Data Type: Status Object
  * Description: The current status descriptors associated with the contact.
  * Constraints:
    * Possible combinations of Domain Status Labels is specified in [@!RFC5733, section 2.2]
    * The value MUST be one of the status tokens defined in the IANA registry for domain statuses.
    * The initial value list MAY be as defined in [@!RFC5733]. In this case the values MUST have the same semantics.

* Postal Information
  * Identifier: postalInfo
  * Cardinality: 1-2
  * Mutability: read-write
  * Data Type: DictionaryAggregation[Postal Info Object]
    * Label Description: type of contact data localisation
    * Label Constraints: Allowed values: "int" for "internationalised" all-ASCII version of an address and "loc" for localised forms with possible non-ASCII character sets.
  * Description: Contains postal-address information.
  * Constraints: There MUST be no more that 1 element of type "int" and one element of type "loc".

* Voice Phone Number
  * Identifier: voice
  * Cardinality: 0+
  * Mutability: read-write
  * Data Type: Phone Number
  * Description: Voice phone number associated with the contact
  * Constraints: (None)

* Fax Phone Number
  * Identifier: fax
  * Cardinality: 0+
  * Mutability: read-write
  * Data Type: Phone Number
  * Description: Fax number associated with the contact
  * Constraints: (None)

* E-mail
  * Identifier: email
  * Cardinality: 0+
  * Mutability: read-write
  * Data Type: String.
  * Description: The contact's email address.
  * Constraints: Email address syntax is defined in [@!RFC5322].

* Authorisation Information
  * Identifier: authInfo
  * Cardinality: 0-1
  * Mutability: read-write
  * Data Type: Authorisation Information
  * Description: Authorisation information associated with the contact object.
  * Constraints: (None)

* Disclose
  * Identifier: disclose
  * Cardinality: 0-1
  * Mutability: read-write
  * Data Type: Disclose Object.
  * Description: Identifies elements that require exceptional server-operator handling to allow or restrict disclosure to third parties.

A> TBC: IANA registry for statuses?

## Operations

A> TODO: Describe CRUD operations for contacts https://github.com/pawel-kow/draft-kowalik-rpp-data-objects/issues/15

### Transfer Operations

The Contact Data Object supports the common transfer operations defined in the [Transfer Operations] section. The transfer of a contact changes the sponsoring client of the contact object.

No object-specific transient data elements are defined for contact transfer operations beyond the common transfer data elements. Specifically, contacts do not have validity periods, so no renewal period or expiry date elements apply.

# Host Data Object

## Object Description

A Host Data Object represents a name server that provides DNS
services for a a domain name.

## Data Elements

The following data elements are defined for the Host Data Object.

* Host Name
  * Identifier: hostName
  * Cardinality: 1
  * Mutability: read-write
  * Data Type: String
  * Description: Fully qualified name of a host.
  * Constraints: The value MUST be a syntactically valid host name.

* Provisioning Metadata
  * Identifier: provisioningMetadata
  * Cardinality: 1
  * Mutability: read-only
  * Data Type: Provisioning Metadata Object
  * Description: Standard metadata about the object's lifecycle and ownership.
  * Constraints: (None)

* Status
  * Identifier: status
  * Cardinality: 0+
  * Mutability: read-only
  * Data Type:  Status Object
  * Description: The current status descriptors associated with the host.
  * Constraints: Possible combinations of Host Status Labels is specified in [@!RFC5732, section 2.3]

* DNS Resource Records
  * Identifier: dns
  * Cardinality: 0+
  * Mutability: read-write
  * Data Type: Composition[DNS Resource Record]
  * Description: DNS Resource Records related to the host. 
  * Constraints: 
    * The labels of DNS entries MUST be subordinate to the Host Name of the Nameserver.
    * In EPP Compatibility Profile the entries MUST be limited to A and AAAA entries for IPv4 and IPv6 glue records respectively.

## Operations

### Create Operation

The Create operation allows a client to provision a new Host Data Object. The operation accepts as input all create-only and read-write data elements defined for the Host Data Object.

* Authorisation:
  * Generally each client is authorised to create new host objects becoming a sponsoring client. This can be however constrained by the server policy, e.g. by applying rate limiting or compliance locks.

If the host name exists in a namespace for which the server is authoritative, then the superordinate domain of the host MUST be known to the server before the host object can be created.

In EPP Compatibility Profile, IP addresses are REQUIRED only as needed to produce DNS glue records. If the host name exists in a namespace for which the server is authoritative and is subordinate to an existing domain, IP addresses SHOULD be provided. If the host name is external to the server's namespace, IP addresses are not required by the DNS and MAY be omitted.

### Read Operation

The Read operation allows a client to retrieve the data elements of a Host Data Object.

* Authorisation:
  * Any client is authorised to retrieve the full object representation. In EPP Compatibility Profile, host objects do not carry authorisation information and there is no distinction based on client identity as described in [@!RFC5732, section 3.1.2].

### Update Operation

The Update operation allows a client to modify the attributes of an existing Host Data Object. The operation targets a specific data object identified by its host name.

* Authorisation:
  * Only sponsoring client is authorised to perform this operation

Host name changes MAY require the addition or removal of IP addresses to be accepted by the server. IP address association MAY be subject to server policies for provisioning hosts as name servers.

Host name changes can have an impact on associated objects that refer to the host object. A host name change SHOULD NOT require additional updates of associated objects to preserve existing associations, with one exception: changing an external host object that has associations with objects that are sponsored by a different client. Attempts to update such hosts directly MUST fail. The change can be provisioned by creating a new external host with a new name and any needed new attributes, and subsequently updating the other objects sponsored by the client.

### Delete Operation

The Delete operation allows a client to remove an existing Host Data Object. The operation targets a specific data object identified by its host name.

* Authorisation:
  * Only sponsoring client is authorised to perform this operation

The server SHOULD reject a delete request if the host object is associated with any other object, such as a domain name object. Deleting a host object without first breaking existing associations can cause DNS resolution failure for domain objects that refer to the deleted host object.

The error response SHOULD indicate the related associated objects.

### Restore Operations

The Host Data Object supports the restore operations defined in the (#restore-ops). These operations are OPTIONAL and are only available when the RGP feature for Host Data Object is supported by the server.

No domain-specific transient data elements extend the common restore operations beyond those defined in the (#restore-ops).

# IANA Considerations

## RPP Data Object Registry

This document establishes the "RESTful Provisioning Protocol (RPP) Data Object Registry". This registry serves as a catalogue of all data objects, component objects, data elements, and operations used within RPP.

### Registration Policy

The policy for adding new objects, data elements, or operations to this registry is "Specification Required" [@!RFC8126].

Standardised RPP extensions that introduce new data objects, add data elements to existing objects, or define new operations or operation parameters MUST register these additions in this registry. Each such registration MUST reference the specification that defines the extension.

Private (non-standardised) extensions are not required to register in this registry.

### Registry Structure

The registry is organised as a collection of Object definitions. Each Object definition MUST include:

* A header containing the Object Identifier, Object Name, Object Type (Resource or Component), a brief description, and a reference to its defining specification.

* A "Data Elements" table listing all persisted data elements associated with the object. Each entry MUST specify the element's Identifier, Name, Cardinality, Mutability, Data Type, description, and a reference to the specification that defines it.

* If applicable, an "Operations" section. For each operation, the
registry MUST provide:
  * The Operation's Name, a description, and a reference to the specification that defines it.
  * A "Parameters" table listing all data elements that are provided as input to the operation but are not persisted as part of the object's state. Each entry MUST specify the parameter's Identifier, Name, Cardinality, Data Type, description, and a reference to the specification that defines it.

Extensions MAY add new data elements, operations, or operation parameters to existing Object definitions in the registry. Each such addition MUST reference the extension specification that introduces it, allowing implementations to distinguish core protocol elements from extension-defined elements.

### Initial Registrations

The initial contents of the RPP Data Object Registry are defined below.

Object: period

Object Name: Period Object

Object Type: Component

Description: Represents a duration of time.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name | Card. | Mutability | Data Type | Description                      |
| ------------------ | ------------ | ----- | ---------- | --------- | -------------------------------- |
| value              | Value        | 1     | read-write | Integer   | The numeric value of the period. |
| unit               | Unit         | 1     | read-write | String    | The unit of the period.          |

Object: dnsrr

Object Name: DNS Resource Record

Object Type: Component

Description: Represents a DNS Entry.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name | Card. | Mutability | Data Type | Description                     |
| ------------------ | ------------ | ----- | ---------- | --------- | ------------------------------- |
| hostNamelabel      | Label        | 1     | read-write | String    | DNS entry label.                |
| type               | Type         | 1     | read-write | String    | DNS entry type.                 |
| data               | Data         | 1     | read-write | String    | DNS entry value.                |
| ttl                | TTL          | 1     | read-write | Number    | TTL value for a reource record. |

Object: authInfo

Object Name: Authorisation Information

Object Type: Component

Description: Contains authorisation credentials for an operation.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name              | Card. | Mutability  | Data Type | Description                                                                                                                                                                               |
| ------------------ | ------------------------- | ----- | ----------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| method             | Method                    | 1     | create-only | String    | The identifier of the RPP authorisation method.                                                                                                                                           |
| authdata           | Authorisation Information | 1     | create-only | String    | The value of the authorisation information. It might be as simple as password string, but also more complex values like public key certificates or tokens encoded as string are possible. |


Object: domainStatus

Object Name: Status Object

Object Type: Component

Description: Represents one of the status values associated with the provisioning object.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name | Card. | Mutability  | Data Type | Description                                                                                                                                                      |
| ------------------ | ------------ | ----- | ----------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| label              | Label        | 1     | create-only | String    | machine-reasible enum label of a status                                                                                                                          |
| reason             | Reason       | 0-1   | create-only | String    | a human-readable text that describes the rationale for the status applied to the object.                                                                         |
| due                | Due          | 0-1   | read-write  | Timestamp | a timestamp, when this status is going to be removed automatically, or changed to other status. This field can be used to expresse lifecycle related information |


Object: provisioningMetadata

Object Name: Provisioning Metadata Object

Object Type: Component

Description: Contains standard metadata about the lifecycle and ownership of a provisioned object.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name         | Card. | Mutability | Data Type         | Description                                                             |
| ------------------ | -------------------- | ----- | ---------- | ----------------- | ----------------------------------------------------------------------- |
| repositoryId       | Repository ID        | 0-1   | read-only  | Identifier        | A server-assigned unique identifier for the object.                     |
| sponsoringClientId | Sponsoring Client ID | 1     | read-only  | Client Identifier | The identifier of the client that is the current sponsor of the object. |
| creatingClientId   | Creating Client ID   | 0-1   | read-only  | Client Identifier | The identifier of the client that created the object.                   |
| creationDate       | Creation Date        | 0-1   | read-only  | Timestamp         | The date and time of object creation.                                   |
| updatingClientId   | Updating Client ID   | 0-1   | read-only  | Client Identifier | The identifier of the client that last updated the object.              |
| updateDate         | Update Date          | 0-1   | read-only  | Timestamp         | The date and time of the most recent object modification.               |
| transferDate       | Transfer Date        | 0-1   | read-only  | Timestamp         | The date and time of the most recent successful object transfer.        |

Object: transferData

Object Name: Transfer Data Object

Object Type: Component

Description: Represents the state of a transfer request for a provisioned object.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name         | Card. | Mutability | Data Type         | Description                                                         |
| ------------------ | -------------------- | ----- | ---------- | ----------------- | ------------------------------------------------------------------- |
| transferStatus     | Transfer Status      | 1     | read-only  | String            | The state of the most recent transfer request.                      |
| transferDirection  | Transfer Direction   | 1     | read-only  | String            | Indicates the direction of the transfer (pull or push).             |
| requestingClientId | Requesting Client ID | 1     | read-only  | Client Identifier | The identifier of the client that initiated the transfer request.   |
| requestDate        | Request Date         | 1     | read-only  | Timestamp         | The date and time that the transfer was requested.                  |
| actingClientId     | Acting Client ID     | 1     | read-only  | Client Identifier | The identifier of the client that should or did act on the request. |
| actionDate         | Action Date          | 1     | read-only  | Timestamp         | The response deadline (if pending) or completion date.              |

A> TODO: IANA table: Postal Address Object
A> TODO: IANA table: Postal Info Object
A> TODO: IANA table: Disclose Object

Object: restoreData

Object Name: Restore Data Object

Object Type: Component

Description: Represents the current state of a restore request for an object that has entered the Redemption Grace Period (RGP). Returned as output of all restore operations. This object is OPTIONAL and is only used when the RGP feature is supported.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name    | Card. | Mutability | Data Type | Description                                                                                                                             |
| ------------------ | --------------- | ----- | ---------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| restoreStatus      | Restore Status  | 1     | read-only  | String    | The current state of the restore process.                                                                                               |
| requestDate        | Request Date    | 0-1   | read-only  | Timestamp | The date and time when the restore request was submitted. Absent if no request has been submitted.                                      |
| reportDate         | Report Date     | 0-1   | read-only  | Timestamp | The date and time when the most recent restore report was accepted. Absent if no report has been accepted.                              |
| reportDueDate      | Report Due Date | 0-1   | read-only  | Timestamp | The deadline for submitting a restore report before the object reverts to redemptionPeriod. Present only when status is pendingRestore. |

Object: restoreReport

Object Name: Restore Report Object

Object Type: Component

Description: Contains the redemption grace period restore report submitted by the sponsoring client as required by the RGP process. This object is OPTIONAL and is only used when the RGP feature is supported and a restore report is required by server policy.

Reference: [This-ID]

Data Elements
| Element Identifier | Element Name      | Card. | Mutability | Data Type | Description                                                                                                        |
| ------------------ | ----------------- | ----- | ---------- | --------- | ------------------------------------------------------------------------------------------------------------------ |
| preData            | Pre-Delete Data   | 0-1   | read-write | String    | A copy of the registration data that existed for the object prior to deletion.                                     |
| postData           | Post-Restore Data | 0-1   | read-write | String    | A copy of the registration data that exists for the the object at the time the restore report is submitted.        |
| deleteTime         | Delete Time       | 0-1   | read-write | Timestamp | The date and time when the object delete request was sent to the server.                                           |
| restoreTime        | Restore Time      | 0-1   | read-write | Timestamp | The date and time when the original restore request operation was sent to the server.                              |
| restoreReason      | Restore Reason    | 0-1   | read-write | String    | A brief explanation of the reason for restoring the object.                                                        |
| statements         | Statements        | 0+    | read-write | String    | Mandatory client statements required by the RGP process. At least one and at most two statements MUST be provided. |
| other              | Other             | 0-1   | read-write | String    | Any additional information needed to support the statements provided by the client.                                |


Object: domainName

Object Name: Domain Name Data Object

Object Type: Resource

Description: Represents a domain name and its associated data.

Reference: [This-ID]

Data Elements
| Identifier           | Name                  | Card. | Mutability  | Data Type                            | Description                                             |
| -------------------- | --------------------- | ----- | ----------- | ------------------------------------ | ------------------------------------------------------- |
| name                 | Name                  | 1     | create-only | String                               | The fully qualified name of the domain object.          |
| provisioningMetadata | Provisioning Metadata | 1     | read-only   | Provisioning Metadata Object         | Standard metadata about object lifecycle and ownership. |
| status               | Status                | 0+    | read-only   | Status Object                        | The current status descriptors for the domain.          |
| registrant           | Registrant            | 0-1   | read-write  | Contact Object                       | The registrant contact ID.                              |
| contacts             | Contacts              | 0+    | read-write  | LabelledAggregation [Contact Object] | Associated contact objects.                             |
| nameservers          | Nameservers           | 0+    | read-write  | Aggregation[Host Data Object]        | A collection of nameservers associated with the domain. |
| dns                  | DNS                   | 0+    | read-write  | Composition[DNS Resource Record]     | A collection of DNS entries related to the domain name. |
| subordinateHosts     | Subordinate Hosts     | 0+    | read-only   | Aggregation [Host Data Object]       | Subordinate host names.                                 |
| expiryDate           | Expiry Date           | 0-1   | read-only   | Timestamp                            | Expiry timestamp.                                       |
| authInfo             | Authorisation Info    | 0-1   | read-write  | authInfo                             | Authorisation information for the object.               |

Operations

Operation: Create

Operation Identifier: create

Description: Provisions a new Domain Name resource.

Parameters
| Identifier | Name                | Card. | Data Type | Description                                          |
| ---------- | ------------------- | ----- | --------- | ---------------------------------------------------- |
| period     | Registration Period | 0-1   | period    | The initial registration period for the domain name. |

Operation: Read

Operation Identifier: read

Description: Retrieves the data elements of a Domain Name resource.

Parameters
| Identifier    | Name                            | Card. | Data Type | Description                                          |
| ------------- | ------------------------------- | ----- | --------- | ---------------------------------------------------- |
| hostsFilter   | Hosts Filter                    | 0-1   | String    | Controls which host information is returned.         |
| queryAuthInfo | Query Authorisation Information | 0-1   | authInfo  | Credentials to authorise access to full object data. |

Operation: Delete

Operation Identifier: delete

Description: Removes an existing Domain Name resource.

Parameters: (None)

Operation: Renew

Operation Identifier: renew

Description: Extends the validity period of a Domain Name resource.

Parameters
| Identifier        | Name                | Card. | Data Type | Description                                       |
| ----------------- | ------------------- | ----- | --------- | ------------------------------------------------- |
| currentExpiryDate | Current Expiry Date | 1     | Timestamp | The expected current expiry date, for validation. |
| renewalPeriod     | Renewal Period      | 0-1   | period    | The duration to add to the registration period.   |

Operation: Transfer Request

Operation Identifier: transferRequest

Description: Initiates a transfer of a Domain Name resource.

Parameters
| Identifier        | Name               | Card. | Data Type         | Description                                                    |
| ----------------- | ------------------ | ----- | ----------------- | -------------------------------------------------------------- |
| transferDirection | Transfer Direction | 0-1   | String            | Indicates whether the transfer is a "pull" or "push" transfer. |
| gainingClientId   | Gaining Client ID  | 0-1   | Client Identifier | The designated gaining client (required for push transfers).   |
| transferPeriod    | Transfer Period    | 0-1   | period            | The duration to add to the registration period upon transfer.  |

Operation: Transfer Approve

Operation Identifier: transferApprove

Description: Approves a pending transfer of a Domain Name resource.

Parameters: (None)

Operation: Transfer Reject

Operation Identifier: transferReject

Description: Rejects a pending transfer of a Domain Name resource.

Parameters
| Identifier | Name   | Card. | Data Type | Description                                                   |
| ---------- | ------ | ----- | --------- | ------------------------------------------------------------- |
| reason     | Reason | 0-1   | String    | A human-readable text describing the rationale for rejection. |

Operation: Transfer Cancel

Operation Identifier: transferCancel

Description: Cancels a pending transfer of a Domain Name resource.

Parameters: (None)

Operation: Transfer Query

Operation Identifier: transferQuery

Description: Queries the status of a transfer of a Domain Name resource.

Parameters: (None)

Operation: Restore Request

Operation Identifier: restoreRequest

Description: Initiates recovery of an domain name in the redemptionPeriod state. This operation is OPTIONAL and is only available when the RGP feature is supported.

Parameters
| Identifier    | Name           | Card. | Data Type             | Description               |
| ------------- | -------------- | ----- | --------------------- | ------------------------- |
| restoreReport | Restore Report | 0-1   | Restore Report Object | An inline restore report. |

Operation: Restore Report

Operation Identifier: restoreReport

Description: Submits the restore report for a domain name in the pendingRestore state. This operation is OPTIONAL and is only available when the RGP feature is supported and the server requires a restore report.

Parameters
| Identifier    | Name           | Card. | Data Type             | Description                         |
| ------------- | -------------- | ----- | --------------------- | ----------------------------------- |
| restoreReport | Restore Report | 1     | Restore Report Object | The restore report to be submitted. |

Operation: Restore Query

Operation Identifier: restoreQuery

Description: Retrieves the current state of the RGP restore process for a domain name. This operation is OPTIONAL and is only available when the RGP feature is supported.

Parameters: (None)

A> TODO: IANA table: Contact Data Object

Object: host

Object Name: Host Data Object

Object Type: Resource

Description: Represents a name server that provides DNS services for a domain name.

Reference: [This-ID]

Data Elements
| Identifier           | Name                  | Card. | Mutability | Data Type                        | Description                                             |
| -------------------- | --------------------- | ----- | ---------- | -------------------------------- | ------------------------------------------------------- |
| hostName             | Host Name             | 1     | read-write | String                           | Fully qualified name of a host.                         |
| provisioningMetadata | Provisioning Metadata | 1     | read-only  | Provisioning Metadata Object     | Standard metadata about object lifecycle and ownership. |
| status               | Status                | 0+    | read-only  | Status Object                    | The current status descriptors for the host.            |
| dns                  | DNS Resource Records  | 0+    | read-write | Composition[DNS Resource Record] | DNS Resource Records related to the host.               |

Operations

Operation: Create

Description: Provisions a new Host Data Object.

Parameters: (None)

Operation: Read

Description: Retrieves the data elements of a Host Data Object.

Parameters: (None)

Operation: Update

Description: Modifies the attributes of a Host Data Object.

Parameters: (None)

Operation: Delete

Description: Removes an existing Host Data Object.

Parameters: (None)

# Security Considerations

A> TODO: write security considerations, if any

{removeInRFC="true"}
{toc="exclude"}
# Changes History

{toc="exclude"}
{numbered="false"}
## draft-kowalik-rpp-data-objects -02 - -03

* integrate RGP features from [@!RFC3915] into main data model and makes it generic for all objects. Restore report inline and optional #48
* abstract common provisioning metadata into reusable component object
* describe operations for hosts #16
* add host/domain relationship terminology from RFC 5732
* remove redundant Nameserver Component Object, domain nameservers use Aggregation[Host Data Object]
* expand extensibility section with standardised/private extension mechanisms, extension points, and operation extensibility
* update IANA registration policy and registry structure to accommodate extension registrations
* change "Aggregation/Composition Dictionary" to "Dictionary Aggregation/Composition" (Issue #32) 
* define common transfer operations and Transfer Data Object with support for pull and push transfers #23
* add domain-specific transfer operations with implicit renewal and subordinate host transfer
* add contact transfer operations referencing common transfer pattern
* add identifiers to all operations

{toc="exclude"}
{numbered="false"}
## draft-kowalik-rpp-data-objects -01 - -02

* ontology of allowed basic datatypes #4
* add examples of associations #31

{backmatter}

<reference anchor="ISO3166-1">
  <front>
    <title>Codes for the representation of names of countries and their subdivisions -- Part 1: Country codes</title>
    <author>
      <organization>International Organization for Standardization</organization>
    </author>
    <date year="2000" month="11"/>
  </front>
  <seriesInfo name="ISO Standard" value="3166"/>
</reference>

<reference anchor="ITU.E164.2005">
  <front>
    <title>The international public telecommunication numbering plan</title>
    <author>
      <organization>International Telecommunication Union</organization>
    </author>
    <date year="2005" month="02"/>
  </front>
  <seriesInfo name="ITU-T Recommendation" value="E.164"/>
</reference>
