from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


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
        self._modules: dict[str, ModuleDefinition] = {}

    def register(self, module: ModuleDefinition) -> ModuleDefinition:
        self._modules[module.module_key] = module
        return module

    def get(self, module_key: str) -> ModuleDefinition | None:
        return self._modules.get(module_key)

    def enable(self, module_key: str) -> ModuleDefinition:
        module = self._modules[module_key]
        self._modules[module_key] = module.model_copy(update={"enabled": True})
        return self._modules[module_key]

    def disable(self, module_key: str) -> ModuleDefinition:
        module = self._modules[module_key]
        self._modules[module_key] = module.model_copy(update={"enabled": False})
        return self._modules[module_key]

    def list(self) -> list[ModuleDefinition]:
        return list(self._modules.values())

    def has(self, module_key: str) -> bool:
        return module_key in self._modules
