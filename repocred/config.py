"""Loading and validation of ``.repocred.yml`` (SCORING.md §8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .rubric import AREA_BY_KEY, MODES, PROFILES

CONFIG_NAMES = (".repocred.yml", ".repocred.yaml")


class ConfigError(ValueError):
    pass


@dataclass
class Config:
    profile: str | None = None          # None => autodetect
    mode: str = "balanced"
    fail_under: float | None = None
    weights: dict[str, int] = field(default_factory=dict)
    checks_off: set[str] = field(default_factory=set)  # areas forced to N/A
    ignore: list[str] = field(default_factory=list)

    @classmethod
    def discover(cls, root: Path) -> Config:
        for name in CONFIG_NAMES:
            path = root / name
            if path.is_file():
                return cls.load(path)
        return cls()

    @classmethod
    def load(cls, path: Path) -> Config:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise ConfigError("PyYAML is required to read .repocred.yml") from exc
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"invalid YAML in {path.name}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigError(f"{path.name} must be a mapping")
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> Config:
        cfg = cls()

        if (profile := raw.get("profile")) is not None:
            if profile not in PROFILES:
                raise ConfigError(f"profile must be one of {PROFILES}, got {profile!r}")
            cfg.profile = profile

        if (mode := raw.get("mode")) is not None:
            if mode not in MODES:
                raise ConfigError(f"mode must be one of {MODES}, got {mode!r}")
            cfg.mode = mode

        if (fu := raw.get("fail_under")) is not None:
            try:
                cfg.fail_under = float(fu)
            except (TypeError, ValueError) as exc:
                raise ConfigError(f"fail_under must be a number, got {fu!r}") from exc
            if not 0 <= cfg.fail_under <= 10:
                raise ConfigError("fail_under must be between 0 and 10")

        weights = raw.get("weights") or {}
        if not isinstance(weights, dict):
            raise ConfigError("weights must be a mapping of area -> integer")
        for area, value in weights.items():
            if area not in AREA_BY_KEY:
                raise ConfigError(f"unknown area in weights: {area!r}")
            if not isinstance(value, int) or value < 0:
                raise ConfigError(f"weight for {area!r} must be a non-negative integer")
        cfg.weights = dict(weights)

        checks = raw.get("checks") or {}
        if not isinstance(checks, dict):
            raise ConfigError("checks must be a mapping of area -> on|off")
        for area, value in checks.items():
            if area not in AREA_BY_KEY:
                raise ConfigError(f"unknown area in checks: {area!r}")
            if value in (False, "off"):
                cfg.checks_off.add(area)

        ignore = raw.get("ignore") or []
        if not isinstance(ignore, list) or not all(isinstance(i, str) for i in ignore):
            raise ConfigError("ignore must be a list of glob strings")
        cfg.ignore = list(ignore)

        return cfg
