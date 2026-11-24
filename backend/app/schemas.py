"""API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TestType = Literal[
    "functional",
    "positive",
    "negative",
    "boundary",
    "edge",
    "error_handling",
    "security",
    "api",
    "ui",
]
Priority = Literal["critical", "high", "medium", "low"]
Risk = Literal["critical", "high", "medium", "low"]
Automation = Literal["high", "medium", "low", "manual_only"]
Origin = Literal["extracted", "inferred"]
CaseStatus = Literal["draft", "reviewed", "approved"]
SourceKind = Literal["user_story", "requirements_document"]
ExportFormat = Literal["xlsx", "csv", "json"]

ALL_TEST_TYPES: list[str] = [
    "functional",
    "positive",
    "negative",
    "boundary",
    "edge",
    "error_handling",
    "security",
    "api",
    "ui",
]


class Finding(BaseModel):
    id: str
    statement: str
    origin: Origin
    evidence: str | None = None
    rationale: str | None = None


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Project name is required")
        return cleaned


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    is_demo: bool
    created_at: datetime
    updated_at: datetime


class SourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: SourceKind
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=100_000)

    @field_validator("title", "content")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value is required")
        return cleaned


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    kind: str
    title: str
    content: str
    created_at: datetime


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    analysis_id: str | None = None
    types: list[TestType] = Field(default_factory=lambda: list(ALL_TEST_TYPES))  # type: ignore[arg-type]
    suite_name: str | None = Field(default=None, max_length=200)

    @field_validator("types")
    @classmethod
    def at_least_one(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("Select at least one test type")
        # Preserve order, drop duplicates.
        seen: list[str] = []
        for item in value:
            if item not in seen:
                seen.append(item)
        return seen

    @field_validator("suite_name")
    @classmethod
    def strip_suite(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class GeneratedCase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=3, max_length=300)
    description: str = Field(default="", max_length=4000)
    requirement_ref: str = Field(default="", max_length=120)
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(min_length=1)
    test_data: dict[str, str] = Field(default_factory=dict)
    expected_result: str = Field(min_length=1, max_length=4000)
    test_type: TestType
    priority: Priority
    risk_level: Risk
    automation_suitability: Automation
    tags: list[str] = Field(default_factory=list)
    scenario_origin: Origin = "inferred"

    @field_validator("preconditions", "steps", "tags")
    @classmethod
    def clean_list(cls, value: list[str]) -> list[str]:
        return [str(item).strip() for item in value if str(item).strip()]

    @field_validator("test_data", mode="before")
    @classmethod
    def stringify_data(cls, value: object) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("test_data must be an object")
        return {str(key): "" if item is None else str(item) for key, item in value.items()}

    @field_validator("steps")
    @classmethod
    def steps_present(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one test step is required")
        return value


class TestCasePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    requirement_ref: str | None = Field(default=None, max_length=120)
    preconditions: list[str] | None = None
    steps: list[str] | None = None
    test_data: dict[str, str] | None = None
    expected_result: str | None = Field(default=None, min_length=1, max_length=4000)
    test_type: TestType | None = None
    priority: Priority | None = None
    risk_level: Risk | None = None
    automation_suitability: Automation | None = None
    tags: list[str] | None = None
    status: CaseStatus | None = None
    suite_id: str | None = None

    @field_validator("test_data")
    @classmethod
    def stringify_patch_data(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        return {str(key): str(item) for key, item in value.items()}


class TestCaseOut(BaseModel):
    id: str
    project_id: str
    suite_id: str | None
    source_id: str | None
    case_key: str
    title: str
    description: str
    requirement_ref: str
    preconditions: list[str]
    steps: list[str]
    test_data: dict
    expected_result: str
    test_type: str
    priority: str
    risk_level: str
    automation_suitability: str
    tags: list[str]
    generation_metadata: dict
    status: str
    created_at: datetime
    updated_at: datetime


class BulkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["delete", "update", "assign_suite"]
    ids: list[str] = Field(min_length=1, max_length=500)
    priority: Priority | None = None
    risk_level: Risk | None = None
    status: CaseStatus | None = None
    suite_id: str | None = None
    tags_add: list[str] = Field(default_factory=list)


class SuiteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Suite name is required")
        return cleaned


class SuitePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)


class SuiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    description: str
    case_count: int
    created_at: datetime


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: ExportFormat
    case_ids: list[str] | None = None
    suite_id: str | None = None


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["mock", "openai", "anthropic"]
    model: str = Field(default="", max_length=120)
    temperature: float = Field(ge=0, le=2)
    max_tokens: int = Field(ge=64, le=8000)


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProviderConfigError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class ProviderRequestError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=502)


class AIOutputError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)
