from __future__ import annotations

from dataclasses import dataclass
import re

from ..models import FieldDefinition, PrototypeContext
from ..utils import slugify, title_case


@dataclass(frozen=True, slots=True)
class ArchetypeDefinition:
    name: str
    keywords: set[str]
    entity_label_singular: str
    entity_label_plural: str
    fields: list[FieldDefinition]
    capabilities: list[str]
    assumptions: list[str]


ARCHETYPES: tuple[ArchetypeDefinition, ...] = (
    ArchetypeDefinition(
        name="feedback_board",
        keywords={"feedback", "suggestion", "vote", "roadmap", "review", "backlog"},
        entity_label_singular="feedback item",
        entity_label_plural="feedback items",
        fields=[
            FieldDefinition("title", "str", "Short summary of the idea"),
            FieldDefinition("description", "str", "Detailed customer or operator context"),
            FieldDefinition("category", "str", "Classification for reporting", required=False, default="general"),
            FieldDefinition("status", "str", "Workflow state", required=False, default="submitted"),
            FieldDefinition("votes", "int", "Relative priority signal", required=False, default=0),
        ],
        capabilities=[
            "capture new feedback items",
            "list the current feedback backlog",
            "inspect item details by identifier",
            "surface metadata for downstream UI clients",
        ],
        assumptions=[
            "The first prototype is intended for an internal product or platform team.",
            "Stakeholders are comfortable ranking work with lightweight vote counts.",
        ],
    ),
    ArchetypeDefinition(
        name="task_manager",
        keywords={"task", "todo", "kanban", "planner", "workflow", "project"},
        entity_label_singular="task",
        entity_label_plural="tasks",
        fields=[
            FieldDefinition("title", "str", "Short task summary"),
            FieldDefinition("description", "str", "Implementation details or notes"),
            FieldDefinition("owner", "str", "Assignee or accountable user"),
            FieldDefinition("priority", "str", "Relative urgency", required=False, default="medium"),
            FieldDefinition("status", "str", "Execution state", required=False, default="planned"),
        ],
        capabilities=[
            "capture new work items",
            "list the work queue",
            "inspect an item by identifier",
            "share machine-readable metadata with a future frontend",
        ],
        assumptions=[
            "The initial release focuses on a single team rather than cross-org dependencies.",
            "Workflow can start with a simple status model before introducing automation.",
        ],
    ),
    ArchetypeDefinition(
        name="inventory_manager",
        keywords={"inventory", "stock", "warehouse", "catalog", "sku", "asset"},
        entity_label_singular="stock item",
        entity_label_plural="stock items",
        fields=[
            FieldDefinition("name", "str", "Human-readable inventory item name"),
            FieldDefinition("sku", "str", "Inventory tracking identifier"),
            FieldDefinition("quantity", "int", "Current quantity on hand"),
            FieldDefinition("location", "str", "Storage location"),
            FieldDefinition("reorder_threshold", "int", "Threshold for replenishment", required=False, default=5),
        ],
        capabilities=[
            "register new stock items",
            "list available inventory",
            "retrieve inventory records by identifier",
            "emit metadata for replenishment-aware clients",
        ],
        assumptions=[
            "A single source of truth for quantity is acceptable during prototyping.",
            "Operators can tolerate in-memory state before database persistence is added.",
        ],
    ),
    ArchetypeDefinition(
        name="appointment_scheduler",
        keywords={"booking", "appointment", "schedule", "reservation", "calendar", "meeting"},
        entity_label_singular="appointment",
        entity_label_plural="appointments",
        fields=[
            FieldDefinition("customer_name", "str", "Customer or attendee name"),
            FieldDefinition("service", "str", "Service or meeting type"),
            FieldDefinition("scheduled_for", "str", "Requested time slot in ISO-8601 form"),
            FieldDefinition("notes", "str", "Context for the booking", required=False, default=""),
            FieldDefinition("status", "str", "Booking lifecycle state", required=False, default="scheduled"),
        ],
        capabilities=[
            "create a booking record",
            "list booked appointments",
            "inspect a booking by identifier",
            "expose scheduling metadata to a future UI",
        ],
        assumptions=[
            "Availability conflicts are handled manually in the first prototype.",
            "Time zones and reminders can be added after the basic booking flow works.",
        ],
    ),
    ArchetypeDefinition(
        name="idea_intake",
        keywords={"idea", "innovation", "proposal", "experiment", "prototype", "product"},
        entity_label_singular="initiative",
        entity_label_plural="initiatives",
        fields=[
            FieldDefinition("title", "str", "Short initiative title"),
            FieldDefinition("problem", "str", "Problem statement"),
            FieldDefinition("target_user", "str", "Primary audience"),
            FieldDefinition("priority", "str", "Relative business importance", required=False, default="medium"),
            FieldDefinition("status", "str", "Current investment stage", required=False, default="discovery"),
        ],
        capabilities=[
            "capture new product initiatives",
            "list the idea pipeline",
            "inspect an initiative by identifier",
            "publish metadata for later product surfaces",
        ],
        assumptions=[
            "The prototype is a discovery artifact instead of a launch-ready product.",
            "A lean intake model is enough until portfolio governance is introduced.",
        ],
    ),
)


def tokenize(idea: str) -> list[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9]+", idea.lower()) if token]


def derive_constraints(tokens: list[str]) -> list[str]:
    constraints: list[str] = [
        "Prototype must run locally with the Python standard library only.",
        "The first release should remain understandable enough for autonomous regeneration.",
    ]
    if any(token in {"enterprise", "admin", "audit"} for token in tokens):
        constraints.append("Role-based access and audit logging will be required before wider rollout.")
    if any(token in {"realtime", "real", "live"} for token in tokens):
        constraints.append("The long-term design needs a path to event-driven or websocket updates.")
    if any(token in {"mobile", "ios", "android"} for token in tokens):
        constraints.append("The API contracts should be stable enough for future mobile clients.")
    if any(token in {"compliance", "hipaa", "pci", "soc2", "gdpr"} for token in tokens):
        constraints.append("Compliance and data-governance controls cannot be deferred in production.")
    return constraints


def derive_product_context(idea: str) -> PrototypeContext:
    tokens = tokenize(idea)
    scored = sorted(
        (
            (
                len(definition.keywords.intersection(tokens)),
                definition,
            )
            for definition in ARCHETYPES
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    _, selected = scored[0]
    product_name = title_case(" ".join(tokens[:6])) or "Autonomous Prototype"
    collection_path = slugify(selected.entity_label_plural)
    return PrototypeContext(
        archetype=selected.name,
        product_name=product_name,
        product_slug=slugify(product_name),
        entity_label_singular=selected.entity_label_singular,
        entity_label_plural=selected.entity_label_plural,
        entity_collection_path=collection_path,
        field_definitions=selected.fields,
        capabilities=selected.capabilities,
        assumptions=selected.assumptions,
        constraints=derive_constraints(tokens),
        keywords=tokens,
    )

