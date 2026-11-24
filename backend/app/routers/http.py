"""HTTP API."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import String, asc, case, cast, delete, desc, func, or_, select
from sqlalchemy.orm import Session

from app.ai.factory import build_provider
from app.config import Settings, get_settings
from app.examples import EXAMPLES
from app.models import (
    AnalysisRecord,
    AppSetting,
    GenerationRun,
    Project,
    RequirementSource,
    TestCaseRecord,
    TestSuite,
    utcnow,
)
from app.schemas import (
    ALL_TEST_TYPES,
    AnalyzeRequest,
    AppError,
    BulkRequest,
    ExportRequest,
    GenerateRequest,
    ProjectCreate,
    ProjectOut,
    SettingsUpdate,
    SourceCreate,
    SourceOut,
    SuiteCreate,
    SuiteOut,
    SuitePatch,
    TestCaseOut,
    TestCasePatch,
)
from app.services.export_service import export_cases
from app.services.quality import coverage_report, find_duplicate_groups
from app.services.seed import seed_demo
from app.services.workflow import store_analysis, store_generation, touch_project

router = APIRouter(prefix="/api")

SORT_FIELDS = {"case_key", "title", "priority", "risk_level", "test_type", "updated_at", "created_at"}
ALLOWED_UPLOADS = {".txt", ".md", ".csv"}


def get_db() -> Session:  # pragma: no cover - replaced in create_app
    raise RuntimeError("Database dependency was not configured")


def get_settings_dep() -> Settings:
    return get_settings()


def ensure_settings(db: Session, settings: Settings) -> AppSetting:
    row = db.get(AppSetting, 1)
    if row is None:
        provider = settings.ai_provider if settings.ai_provider in {"mock", "openai", "anthropic"} else "mock"
        row = AppSetting(
            id=1,
            provider=provider,
            model="",
            temperature=settings.generation_temperature,
            max_tokens=settings.generation_max_tokens,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_provider(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
):
    row = ensure_settings(db, settings)
    return build_provider(settings, row.provider, row.model)


def _project_or_404(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _source_or_404(db: Session, project_id: str, source_id: str) -> RequirementSource:
    source = db.get(RequirementSource, source_id)
    if source is None or source.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement source not found")
    return source


def _case_out(row: TestCaseRecord) -> TestCaseOut:
    return TestCaseOut(
        id=row.id,
        project_id=row.project_id,
        suite_id=row.suite_id,
        source_id=row.source_id,
        case_key=row.case_key,
        title=row.title,
        description=row.description or "",
        requirement_ref=row.requirement_ref or "",
        preconditions=list(row.preconditions or []),
        steps=list(row.steps or []),
        test_data=dict(row.test_data or {}),
        expected_result=row.expected_result or "",
        test_type=row.test_type,
        priority=row.priority,
        risk_level=row.risk_level,
        automation_suitability=row.automation_suitability,
        tags=list(row.tags or []),
        generation_metadata=dict(row.generation_metadata or {}),
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _case_dict(row: TestCaseRecord) -> dict:
    return _case_out(row).model_dump(mode="json")


def _suite_out(db: Session, row: TestSuite) -> SuiteOut:
    count = db.scalar(select(func.count()).select_from(TestCaseRecord).where(TestCaseRecord.suite_id == row.id))
    return SuiteOut(
        id=row.id,
        project_id=row.project_id,
        name=row.name,
        description=row.description or "",
        case_count=int(count or 0),
        created_at=row.created_at,
    )


@router.get("/health")
def health(db: Session = Depends(get_db), settings: Settings = Depends(get_settings_dep)) -> dict:
    row = ensure_settings(db, settings)
    return {
        "status": "ok",
        "database": "ok",
        "provider": row.provider,
        "provider_mode": "deterministic-mock" if row.provider == "mock" else "external-adapter",
        "version": "1.0.0",
    }


@router.get("/examples")
def examples() -> dict:
    return {"examples": EXAMPLES}


@router.get("/settings")
def read_settings(db: Session = Depends(get_db), settings: Settings = Depends(get_settings_dep)) -> dict:
    row = ensure_settings(db, settings)
    return _settings_payload(row, settings)


@router.put("/settings")
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> dict:
    row = ensure_settings(db, settings)
    row.provider = body.provider
    row.model = body.model.strip()
    row.temperature = body.temperature
    row.max_tokens = body.max_tokens
    db.add(row)
    db.commit()
    db.refresh(row)
    return _settings_payload(row, settings)


def _settings_payload(row: AppSetting, settings: Settings) -> dict:
    active_model = row.model
    if not active_model:
        if row.provider == "mock":
            active_model = "deterministic-rules-v1"
        elif row.provider == "openai":
            active_model = settings.openai_model
        else:
            active_model = settings.anthropic_model
    return {
        "provider": row.provider,
        "model": row.model,
        "active_model": active_model,
        "temperature": row.temperature,
        "max_tokens": row.max_tokens,
        "temperature_applied_to_mock": False,
        "secrets_accepted_from_browser": False,
        "providers": [
            {
                "id": "mock",
                "configured": True,
                "description": "Deterministic local rules. No external API and no API key.",
            },
            {
                "id": "openai",
                "configured": bool(settings.openai_api_key),
                "description": "Uses OPENAI_API_KEY from the server environment. The key is not returned by this API.",
            },
            {
                "id": "anthropic",
                "configured": bool(settings.anthropic_api_key),
                "description": "Uses ANTHROPIC_API_KEY from the server environment. The key is not returned by this API.",
            },
        ],
    }


@router.post("/demo/seed", response_model=ProjectOut)
def create_demo(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    provider=Depends(get_provider),
) -> Project:
    row = ensure_settings(db, settings)
    try:
        return seed_demo(db, provider, row.temperature, row.max_tokens)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return list(db.scalars(select(Project).order_by(desc(Project.updated_at))).all())


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(name=body.name, description=body.description, is_demo=False)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)) -> Project:
    return _project_or_404(db, project_id)


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)) -> Response:
    _project_or_404(db, project_id)
    db.execute(delete(TestCaseRecord).where(TestCaseRecord.project_id == project_id))
    db.execute(delete(TestSuite).where(TestSuite.project_id == project_id))
    db.execute(delete(AnalysisRecord).where(AnalysisRecord.project_id == project_id))
    db.execute(delete(GenerationRun).where(GenerationRun.project_id == project_id))
    db.execute(delete(RequirementSource).where(RequirementSource.project_id == project_id))
    db.execute(delete(Project).where(Project.id == project_id))
    db.commit()
    return Response(status_code=204)


@router.get("/projects/{project_id}/summary")
def project_summary(project_id: str, db: Session = Depends(get_db)) -> dict:
    project = _project_or_404(db, project_id)
    cases = list(db.scalars(select(TestCaseRecord).where(TestCaseRecord.project_id == project_id)).all())
    by_type: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for item in cases:
        by_type[item.test_type] = by_type.get(item.test_type, 0) + 1
        by_priority[item.priority] = by_priority.get(item.priority, 0) + 1
        by_risk[item.risk_level] = by_risk.get(item.risk_level, 0) + 1
    latest_analysis = db.scalars(
        select(AnalysisRecord)
        .where(AnalysisRecord.project_id == project_id)
        .order_by(desc(AnalysisRecord.created_at))
    ).first()
    latest_run = db.scalars(
        select(GenerationRun)
        .where(GenerationRun.project_id == project_id)
        .order_by(desc(GenerationRun.created_at))
    ).first()
    coverage = coverage_report(latest_analysis.payload if latest_analysis else None, [_case_dict(item) for item in cases])
    return {
        "project": ProjectOut.model_validate(project, from_attributes=True).model_dump(mode="json"),
        "counts": {
            "test_cases": len(cases),
            "suites": int(
                db.scalar(select(func.count()).select_from(TestSuite).where(TestSuite.project_id == project_id)) or 0
            ),
            "sources": int(
                db.scalar(
                    select(func.count()).select_from(RequirementSource).where(RequirementSource.project_id == project_id)
                )
                or 0
            ),
            "analyses": int(
                db.scalar(
                    select(func.count()).select_from(AnalysisRecord).where(AnalysisRecord.project_id == project_id)
                )
                or 0
            ),
        },
        "by_type": by_type,
        "by_priority": by_priority,
        "by_risk": by_risk,
        "coverage": coverage,
        "latest_run": None
        if latest_run is None
        else {
            "id": latest_run.id,
            "provider": latest_run.provider,
            "model": latest_run.model,
            "status": latest_run.status,
            "stats": latest_run.stats,
            "parameters": latest_run.parameters,
            "error": latest_run.error,
            "created_at": latest_run.created_at.isoformat() if latest_run.created_at else None,
        },
    }


@router.post("/projects/{project_id}/sources", response_model=SourceOut, status_code=201)
def create_source(project_id: str, body: SourceCreate, db: Session = Depends(get_db)) -> RequirementSource:
    project = _project_or_404(db, project_id)
    source = RequirementSource(project_id=project.id, kind=body.kind, title=body.title, content=body.content)
    db.add(source)
    touch_project(db, project)
    db.commit()
    db.refresh(source)
    return source


@router.post("/projects/{project_id}/sources/upload", response_model=SourceOut, status_code=201)
async def upload_source(
    project_id: str,
    file: UploadFile = File(...),
    kind: str = Form(...),
    title: str = Form(""),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
) -> RequirementSource:
    if kind not in {"user_story", "requirements_document"}:
        raise HTTPException(status_code=422, detail="kind must be user_story or requirements_document")
    project = _project_or_404(db, project_id)
    safe_name = Path(file.filename or "upload.txt").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_UPLOADS:
        raise HTTPException(status_code=415, detail="Upload a .txt, .md, or .csv text file.")
    raw = await file.read(settings.max_upload_bytes + 1)
    await file.close()
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the input size limit.")
    if b"\x00" in raw:
        raise HTTPException(status_code=422, detail="File is not plain text.")
    try:
        content = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="File must be UTF-8 text.") from exc
    if not content:
        raise HTTPException(status_code=422, detail="File is empty.")
    if len(content) > settings.max_input_chars:
        raise HTTPException(status_code=422, detail="Text exceeds the input size limit.")
    source = RequirementSource(
        project_id=project.id,
        kind=kind,
        title=(title or Path(safe_name).stem or "Uploaded requirements").strip()[:300],
        content=content,
    )
    db.add(source)
    touch_project(db, project)
    db.commit()
    db.refresh(source)
    return source


@router.get("/projects/{project_id}/sources", response_model=list[SourceOut])
def list_sources(project_id: str, db: Session = Depends(get_db)) -> list[RequirementSource]:
    _project_or_404(db, project_id)
    return list(
        db.scalars(
            select(RequirementSource)
            .where(RequirementSource.project_id == project_id)
            .order_by(desc(RequirementSource.created_at))
        ).all()
    )


@router.post("/projects/{project_id}/analyze")
def analyze(project_id: str, body: AnalyzeRequest, db: Session = Depends(get_db)) -> dict:
    _project_or_404(db, project_id)
    source = _source_or_404(db, project_id, body.source_id)
    row = store_analysis(db, project_id, source.id, source.content, source.kind)
    return {"id": row.id, "project_id": project_id, "source_id": source.id, "payload": row.payload}


@router.get("/projects/{project_id}/analyses")
def list_analyses(project_id: str, db: Session = Depends(get_db)) -> dict:
    _project_or_404(db, project_id)
    rows = db.scalars(
        select(AnalysisRecord).where(AnalysisRecord.project_id == project_id).order_by(desc(AnalysisRecord.created_at))
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "project_id": row.project_id,
                "source_id": row.source_id,
                "payload": row.payload,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.post("/projects/{project_id}/generate")
def generate(
    project_id: str,
    body: GenerateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    provider=Depends(get_provider),
) -> dict:
    project = _project_or_404(db, project_id)
    source = _source_or_404(db, project_id, body.source_id)
    row_settings = ensure_settings(db, settings)
    if body.analysis_id:
        analysis = db.get(AnalysisRecord, body.analysis_id)
        if analysis is None or analysis.project_id != project_id or analysis.source_id != source.id:
            raise HTTPException(status_code=404, detail="Analysis not found for this source")
    else:
        analysis = db.scalars(
            select(AnalysisRecord)
            .where(AnalysisRecord.source_id == source.id)
            .order_by(desc(AnalysisRecord.created_at))
        ).first()
        if analysis is None:
            analysis = store_analysis(db, project_id, source.id, source.content, source.kind)
    try:
        run, records, suite = store_generation(
            db,
            project_id=project.id,
            source_id=source.id,
            analysis=analysis,
            selected_types=list(body.types),
            suite_name=body.suite_name,
            provider=provider,
            temperature=row_settings.temperature,
            max_tokens=row_settings.max_tokens,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    touch_project(db, project)
    db.commit()
    return {
        "run_id": run.id,
        "provider": run.provider,
        "model": run.model,
        "status": run.status,
        "stats": run.stats,
        "analysis_id": analysis.id,
        "suite_id": suite.id if suite else None,
        "test_cases": [_case_dict(record) for record in records],
    }


@router.get("/projects/{project_id}/test-cases")
def list_cases(
    project_id: str,
    db: Session = Depends(get_db),
    q: str = Query(default="", max_length=200),
    test_type: str | None = None,
    priority: str | None = None,
    risk_level: str | None = None,
    suite_id: str | None = None,
    status: str | None = None,
    sort: str = "case_key",
    order: str = "asc",
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    _project_or_404(db, project_id)
    if sort not in SORT_FIELDS:
        raise HTTPException(status_code=422, detail="Unsupported sort field")
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="Unsupported sort order")
    if test_type and test_type not in ALL_TEST_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported test type")
    filters = [TestCaseRecord.project_id == project_id]
    if test_type:
        filters.append(TestCaseRecord.test_type == test_type)
    if priority:
        filters.append(TestCaseRecord.priority == priority)
    if risk_level:
        filters.append(TestCaseRecord.risk_level == risk_level)
    if suite_id:
        filters.append(TestCaseRecord.suite_id == suite_id)
    if status:
        filters.append(TestCaseRecord.status == status)
    if q.strip():
        like = f"%{q.strip().lower()}%"
        filters.append(
            or_(
                func.lower(TestCaseRecord.title).like(like),
                func.lower(TestCaseRecord.description).like(like),
                func.lower(TestCaseRecord.requirement_ref).like(like),
                func.lower(cast(TestCaseRecord.tags, String)).like(like),
            )
        )
    priority_rank = case(
        (TestCaseRecord.priority == "critical", 0),
        (TestCaseRecord.priority == "high", 1),
        (TestCaseRecord.priority == "medium", 2),
        (TestCaseRecord.priority == "low", 3),
        else_=4,
    )
    risk_rank = case(
        (TestCaseRecord.risk_level == "critical", 0),
        (TestCaseRecord.risk_level == "high", 1),
        (TestCaseRecord.risk_level == "medium", 2),
        (TestCaseRecord.risk_level == "low", 3),
        else_=4,
    )
    sort_map = {
        "case_key": TestCaseRecord.case_key,
        "title": TestCaseRecord.title,
        "priority": priority_rank,
        "risk_level": risk_rank,
        "test_type": TestCaseRecord.test_type,
        "updated_at": TestCaseRecord.updated_at,
        "created_at": TestCaseRecord.created_at,
    }
    direction = asc if order == "asc" else desc
    total = int(db.scalar(select(func.count()).select_from(TestCaseRecord).where(*filters)) or 0)
    rows = db.scalars(
        select(TestCaseRecord).where(*filters).order_by(direction(sort_map[sort])).limit(limit).offset(offset)
    ).all()
    return {"items": [_case_dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/test-cases/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)) -> dict:
    row = db.get(TestCaseRecord, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return _case_dict(row)


@router.patch("/test-cases/{case_id}")
def update_case(case_id: str, body: TestCasePatch, db: Session = Depends(get_db)) -> dict:
    row = db.get(TestCaseRecord, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    data = body.model_dump(exclude_unset=True)
    if "suite_id" in data and data["suite_id"]:
        suite = db.get(TestSuite, data["suite_id"])
        if suite is None or suite.project_id != row.project_id:
            raise HTTPException(status_code=422, detail="Suite does not belong to this project")
    if "steps" in data and data["steps"] is not None and len(data["steps"]) == 0:
        raise HTTPException(status_code=422, detail="At least one test step is required")
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return _case_dict(row)


@router.delete("/test-cases/{case_id}", status_code=204)
def delete_case(case_id: str, db: Session = Depends(get_db)) -> Response:
    row = db.get(TestCaseRecord, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.post("/projects/{project_id}/test-cases/bulk")
def bulk_cases(project_id: str, body: BulkRequest, db: Session = Depends(get_db)) -> dict:
    _project_or_404(db, project_id)
    rows = list(
        db.scalars(
            select(TestCaseRecord).where(
                TestCaseRecord.project_id == project_id,
                TestCaseRecord.id.in_(body.ids),
            )
        ).all()
    )
    if len(rows) != len(set(body.ids)):
        raise HTTPException(status_code=404, detail="One or more test cases were not found in this project")
    if body.action == "delete":
        for row in rows:
            db.delete(row)
        db.commit()
        return {"affected": len(rows)}
    if body.action == "assign_suite":
        if body.suite_id:
            suite = db.get(TestSuite, body.suite_id)
            if suite is None or suite.project_id != project_id:
                raise HTTPException(status_code=422, detail="Suite does not belong to this project")
        for row in rows:
            row.suite_id = body.suite_id
            row.updated_at = utcnow()
        db.commit()
        return {"affected": len(rows)}
    if body.priority is None and body.risk_level is None and body.status is None and not body.tags_add:
        raise HTTPException(status_code=422, detail="Provide a field to update")
    for row in rows:
        if body.priority:
            row.priority = body.priority
        if body.risk_level:
            row.risk_level = body.risk_level
        if body.status:
            row.status = body.status
        if body.tags_add:
            tags = list(row.tags or [])
            for tag in body.tags_add:
                cleaned = tag.strip()
                if cleaned and cleaned not in tags:
                    tags.append(cleaned)
            row.tags = tags
        row.updated_at = utcnow()
    db.commit()
    return {"affected": len(rows)}


@router.get("/projects/{project_id}/duplicates")
def duplicates(project_id: str, db: Session = Depends(get_db)) -> dict:
    _project_or_404(db, project_id)
    rows = list(db.scalars(select(TestCaseRecord).where(TestCaseRecord.project_id == project_id)).all())
    return {
        "method": "token_jaccard",
        "threshold": 0.8,
        "note": "Groups share similar titles. This is a lexical check, not a model similarity score.",
        "groups": find_duplicate_groups([_case_dict(row) for row in rows]),
    }


@router.get("/projects/{project_id}/coverage")
def coverage(project_id: str, db: Session = Depends(get_db)) -> dict:
    _project_or_404(db, project_id)
    analysis = db.scalars(
        select(AnalysisRecord).where(AnalysisRecord.project_id == project_id).order_by(desc(AnalysisRecord.created_at))
    ).first()
    cases = list(db.scalars(select(TestCaseRecord).where(TestCaseRecord.project_id == project_id)).all())
    return coverage_report(analysis.payload if analysis else None, [_case_dict(row) for row in cases])


@router.get("/projects/{project_id}/suites", response_model=list[SuiteOut])
def list_suites(project_id: str, db: Session = Depends(get_db)) -> list[SuiteOut]:
    _project_or_404(db, project_id)
    rows = db.scalars(select(TestSuite).where(TestSuite.project_id == project_id).order_by(TestSuite.name)).all()
    return [_suite_out(db, row) for row in rows]


@router.post("/projects/{project_id}/suites", response_model=SuiteOut, status_code=201)
def create_suite(project_id: str, body: SuiteCreate, db: Session = Depends(get_db)) -> SuiteOut:
    project = _project_or_404(db, project_id)
    row = TestSuite(project_id=project.id, name=body.name, description=body.description)
    db.add(row)
    touch_project(db, project)
    db.commit()
    db.refresh(row)
    return _suite_out(db, row)


@router.patch("/suites/{suite_id}", response_model=SuiteOut)
def update_suite(suite_id: str, body: SuitePatch, db: Session = Depends(get_db)) -> SuiteOut:
    row = db.get(TestSuite, suite_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Suite not found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _suite_out(db, row)


@router.delete("/suites/{suite_id}", status_code=204)
def delete_suite(suite_id: str, db: Session = Depends(get_db)) -> Response:
    row = db.get(TestSuite, suite_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Suite not found")
    linked = db.scalars(select(TestCaseRecord).where(TestCaseRecord.suite_id == row.id)).all()
    for case in linked:
        case.suite_id = None
        case.updated_at = utcnow()
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.post("/projects/{project_id}/exports")
def export_project(project_id: str, body: ExportRequest, db: Session = Depends(get_db)) -> Response:
    project = _project_or_404(db, project_id)
    filters = [TestCaseRecord.project_id == project_id]
    if body.case_ids:
        filters.append(TestCaseRecord.id.in_(body.case_ids))
    if body.suite_id:
        filters.append(TestCaseRecord.suite_id == body.suite_id)
    rows = list(db.scalars(select(TestCaseRecord).where(*filters).order_by(TestCaseRecord.case_key)).all())
    if body.case_ids and len(rows) != len(set(body.case_ids)):
        raise HTTPException(status_code=404, detail="One or more test cases were not found in this project")
    data, media, filename = export_cases(
        project.name,
        project.id,
        project.is_demo,
        [_case_dict(row) for row in rows],
        body.format,
    )
    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
