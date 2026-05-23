from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from apps.backend.app.persistence_repos import ModuleRegistryRepository


class ModuleDefinition(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    module_key: str
    module_name: str
    version: str
    enabled: bool = True
    config_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_key(self) -> "ModuleDefinition":
        if not self.module_key.strip():
            raise ValueError("module_key must not be empty")
        if not self.module_name.strip():
            raise ValueError("module_name must not be empty")
        if not self.version.strip():
            raise ValueError("version must not be empty")
        return self

    def as_registration_payload(self) -> dict[str, Any]:
        return {
            "module_key": self.module_key,
            "module_name": self.module_name,
            "version": self.version,
            "enabled": self.enabled,
            "config_json": self.config_json,
        }


class ModuleRegistry:
    def __init__(self) -> None:
        self.repo = ModuleRegistryRepository()

    def register(self, module: ModuleDefinition) -> ModuleDefinition:
        self.repo.upsert(module.module_key, module.model_dump(mode="json"))
        return module

    def get(self, module_key: str) -> ModuleDefinition | None:
        payload = self.repo.get(module_key)
        return ModuleDefinition.model_validate(payload) if payload else None

    def enable(self, module_key: str) -> ModuleDefinition:
        module = self.get(module_key)
        if module is None:
            raise KeyError(module_key)
        updated = module.model_copy(update={"enabled": True})
        self.repo.upsert(module_key, updated.model_dump(mode="json"))
        return updated

    def disable(self, module_key: str) -> ModuleDefinition:
        module = self.get(module_key)
        if module is None:
            raise KeyError(module_key)
        updated = module.model_copy(update={"enabled": False})
        self.repo.upsert(module_key, updated.model_dump(mode="json"))
        return updated

    def list(self) -> list[ModuleDefinition]:
        return [ModuleDefinition.model_validate(item) for item in self.repo.list_all()]

    def has(self, module_key: str) -> bool:
        return self.get(module_key) is not None
