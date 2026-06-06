#!/usr/bin/env python3
"""Generate the catalog ``index.json`` from the ``packages/`` tree.

The ACC catalog resolver (https mode) fetches ``<catalog-url>/index.json``
and reads one row per package: ``name``, ``version``, ``tarball_sha256``,
``tarball_url`` and — for the signing floor — the signature artefacts.

This repo publishes **both** signature types (operator decision, 2026-06-05):

* ``signature_url`` → the cosign **keypair** ``.sig`` (verified against
  ``keys/acc-ecosystem.pub``; the air-gap / pinned-key path, D3).
* ``bundle_url``    → the cosign keyless **.bundle** (cert + Rekor proof;
  verified against the GitHub Actions OIDC identity).

A consumer's catalog ``required_signer`` decides which one it uses:
keypair-mode reads ``signature_url``, keyless-mode reads ``bundle_url``.

Usage::

    python tools/gen_index.py                 # write ./index.json
    python tools/gen_index.py --check         # fail if index.json is stale
    python tools/gen_index.py -o /tmp/i.json  # write elsewhere

URL paths are emitted root-relative (``/packages/<scope>/<file>``) so the
same index works whether the tree is served from GitHub Pages, a Release
asset mirror, or an internal hub — the resolver joins them under the
catalog's own base URL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# ``<name>-<version>.accpkg`` — must match acc/pkg/catalog._ACCPKG_RE so the
# file-mode and https-mode views of the same tree agree on (name, version).
_ACCPKG_RE = re.compile(
    r"^(?P<name>[^/]+)-(?P<version>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\.accpkg$"
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1


def _sha256(path: Path) -> str:
    """Prefer the committed ``.sha256`` sidecar; fall back to computing it."""
    sidecar = path.with_suffix(".accpkg.sha256")
    if sidecar.is_file():
        return sidecar.read_text(encoding="utf-8").strip().split()[0]
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_index(repo_root: Path = _REPO_ROOT) -> dict:
    packages_dir = repo_root / "packages"
    rows: list[dict] = []
    if packages_dir.is_dir():
        for scope_dir in sorted(packages_dir.iterdir()):
            if not scope_dir.is_dir():
                continue
            scope = scope_dir.name
            for accpkg in sorted(scope_dir.glob("*.accpkg")):
                m = _ACCPKG_RE.match(accpkg.name)
                if not m:
                    print(
                        f"warning: skipping unparseable package name {accpkg.name!r}",
                        file=sys.stderr,
                    )
                    continue
                rel = f"/packages/{scope}/{accpkg.name}"
                row = {
                    "name": f"@{scope}/{m['name']}",
                    "version": m["version"],
                    "tarball_sha256": _sha256(accpkg),
                    "tarball_url": rel,
                }
                sig = accpkg.with_suffix(".accpkg.sig")
                if sig.is_file():
                    row["signature_url"] = rel + ".sig"
                bundle = accpkg.with_suffix(".accpkg.bundle")
                if bundle.is_file():
                    row["bundle_url"] = rel + ".bundle"
                rows.append(row)
    rows.sort(key=lambda r: (r["name"], r["version"]))
    return {"schema_version": SCHEMA_VERSION, "packages": rows}


def _render(index: dict) -> str:
    return json.dumps(index, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", type=Path, default=_REPO_ROOT / "index.json",
        help="output path (default: ./index.json)",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="don't write; exit non-zero if the existing index.json is stale",
    )
    args = parser.parse_args(argv)

    index = build_index()
    rendered = _render(index)

    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.is_file() else ""
        if current != rendered:
            print(
                f"error: {args.output} is stale — run "
                "`python tools/gen_index.py` and commit the result",
                file=sys.stderr,
            )
            return 1
        print(f"ok: {args.output} is up to date ({len(index['packages'])} packages)")
        return 0

    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output} ({len(index['packages'])} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
