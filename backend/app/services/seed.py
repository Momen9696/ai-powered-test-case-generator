"""Seed a clearly labeled demo project."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.examples import SAMPLE_TRANSFER_STORY
from app.models import Project, RequirementSource
from app.services.workflow import store_analysis, store_generation

DEMO_NAME = "Demo — Account transfer"


def seed_demo(db: Session, provider: AIProvider, temperature: float, max_tokens: int) -> Project:
    existing = db.scalars(select(Project).where(Project.is_demo.is_(True), Project.name == DEMO_NAME)).first()
    if existing:
        return existing
    project = Project(
        name=DEMO_NAME,
        description=(
            "Sample project shipped for local demonstration. "
            "Test cases are produced by the active provider when the seed runs. "
            "The default provider is the deterministic mock, not an external model."
        ),
        is_demo=True,
    )
    db.add(project)
    db.flush()
    source = RequirementSource(
        project_id=project.id,
        kind="user_story",
        title="Transfer money between accounts",
        content=SAMPLE_TRANSFER_STORY.strip(),
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    analysis = store_analysis(db, project.id, source.id, source.content, source.kind)
    store_generation(
        db,
        project_id=project.id,
        source_id=source.id,
        analysis=analysis,
        selected_types=[
            "functional",
            "positive",
            "negative",
            "boundary",
            "edge",
            "error_handling",
            "security",
            "api",
            "ui",
        ],
        suite_name="Account transfer — generated suite",
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    db.refresh(project)
    return project
