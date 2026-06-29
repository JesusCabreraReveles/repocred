"""Area 5 — License (GitHub / SPDX)."""

from __future__ import annotations

import re

from ..context import RepoContext
from ..model import CheckResult
from ._util import not_found, read_manifest, result

_LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md", "COPYING", "COPYING.md")

# Markers that map license text to an SPDX id (high precision).
_SPDX_MARKERS = [
    ("MIT", re.compile(r"\bMIT License\b|Permission is hereby granted, free of charge")),
    ("Apache-2.0", re.compile(r"Apache License,?\s+Version 2\.0")),
    ("GPL-3.0", re.compile(r"GNU GENERAL PUBLIC LICENSE\s+Version 3")),
    ("GPL-2.0", re.compile(r"GNU GENERAL PUBLIC LICENSE\s+Version 2")),
    ("AGPL-3.0", re.compile(r"GNU AFFERO GENERAL PUBLIC LICENSE")),
    ("LGPL-3.0", re.compile(r"GNU LESSER GENERAL PUBLIC LICENSE")),
    ("BSD-3-Clause", re.compile(r"Redistribution and use in source and binary forms.*Neither the name", re.S)),
    ("BSD-2-Clause", re.compile(r"Redistribution and use in source and binary forms")),
    ("ISC", re.compile(r"\bISC License\b|Permission to use, copy, modify, and/or distribute")),
    ("MPL-2.0", re.compile(r"Mozilla Public License Version 2\.0")),
    ("Unlicense", re.compile(r"This is free and unencumbered software released into the public domain")),
]
_MANIFEST_LICENSE = re.compile(r'(?i)license\s*[:=]\s*["\']?\s*([A-Za-z0-9.\-+]+)')


def evaluate(ctx: RepoContext) -> list[CheckResult]:
    path = ctx.find(*_LICENSE_NAMES)
    if not path:
        nf = not_found(*_LICENSE_NAMES[:3])
        return [result("license.present", 0, nf), result("license.spdx", 0, nf)]

    present = result("license.present", 6, path)
    text = ctx.read(path) or ""

    spdx_id = None
    for sid, pat in _SPDX_MARKERS:
        if pat.search(text):
            spdx_id = sid
            break
    if not spdx_id:
        manifest = read_manifest(ctx)
        if manifest:
            m = _MANIFEST_LICENSE.search(manifest[1])
            if m and m.group(1).lower() not in ("none", "proprietary", "unlicensed"):
                spdx_id = m.group(1)

    spdx = result("license.spdx", 2 if spdx_id else 0,
                  f"{path}: {spdx_id}" if spdx_id else f"{path}: license not recognized as SPDX")
    return [present, spdx]
