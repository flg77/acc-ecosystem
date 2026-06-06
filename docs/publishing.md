# Publishing & signing family packs

How a signed `.accpkg` gets from a built artifact to the live catalog at
`https://flg77.github.io/acc-ecosystem`.

## The signing model — "publish both"

Every pack is signed **two** ways and both artifacts are published:

| Artifact | cosign mode | Verified against | index.json field | Use |
|----------|-------------|------------------|------------------|-----|
| `<pkg>.sig` | keypair (`--key`) | `keys/acc-ecosystem.pub` | `signature_url` | air-gap / pinned-key (D3) |
| `<pkg>.bundle` | keyless (OIDC `--bundle`) | GitHub Actions OIDC identity | `bundle_url` | connected / no key custody |

A consumer's catalog `required_signer` decides which one it verifies:
keyless-mode (`issuer` + `subject_pattern`) reads `bundle_url`; keypair-mode
(`key_path`) reads `signature_url`. The verifier contract lives in
`agentic-cell-corpus/acc/pkg/verify.py`.

> **cosign is pinned to v2** (`COSIGN_RELEASE` in the workflow). `acc/pkg/verify.py`
> uses v2 `verify-blob` semantics — `--key` does not query Rekor, and air-gap
> verification adds `--insecure-ignore-tlog`. cosign v3 changed the tlog
> defaults and would break that contract.

### Why keyless signing must run in CI

The canonical catalog requires the bundle's certificate identity to match:

```
subject_pattern: "^https://github\\.com/flg77/acc-ecosystem/"
```

Only the **GitHub Actions OIDC token** mints a Fulcio cert with that identity.
A `cosign sign-blob` run on a laptop embeds the operator's *personal* OIDC
identity (Google/GitHub user) and the catalog would reject it. **Therefore the
`.bundle` is always produced by `publish-family-packs.yml`, never by hand.**
The keypair `.sig` has no such constraint and can be made locally.

## One-time setup

1. **Repo secrets** (Settings → Secrets and variables → Actions):
   - `COSIGN_PRIVATE_KEY` — the cosign keypair private key PEM
   - `COSIGN_PASSWORD` — its passphrase

   The matching public key is committed at `keys/acc-ecosystem.pub`. The
   private key otherwise lives only on the lighthouse host
   (`~/.config/acc/signing/`, chmod 600).

2. **Pages source** → set GitHub Pages to deploy from the **`gh-pages`**
   branch, root (`/`). The workflow pushes the published tree (`index.json`,
   `packages/`, `keys/`) there; `main` no longer carries hand-committed
   signatures.

## Publishing flow (every release)

1. **Build** the packs in an `acc-ecosystem-spearhead` checkout (role sources +
   manifests live there). Example for the seven corporate domain packs:

   ```bash
   for d in hr finance sales marketing legal support operations; do
     python tools/build_family_pkg.py --manifest manifests/$d.yaml \
       --repo-root . --version 1.0.0 \
       --output dist/$d-roles-1.0.0.accpkg
   done
   ```

   The `@acc/business-roles@2.0.0` umbrella is a manifest with `depends_on`
   (the seven domain packs) and no roles — build it from its umbrella
   `accpkg.yaml` with `python -m acc.pkg.cli build <src> -o dist/business-roles-2.0.0.accpkg`.

2. **Commit** each `<pkg>.accpkg` **and** its `<pkg>.accpkg.sha256` under
   `packages/acc/` in this repo. (Generate the sha256 with
   `sha256sum pkg > pkg.sha256` or let the build emit it.)

3. **Tag** `vX.Y.Z` and push. The tag triggers `publish-family-packs.yml`,
   which: keypair-signs (`.sig`) + keyless-signs (`.bundle`) every pack,
   regenerates `index.json` (`python tools/gen_index.py`), deploys the tree to
   `gh-pages`, and uploads a Release. `index.json` ends up advertising both
   `signature_url` and `bundle_url` for every entry.

### Optional: commit the keypair `.sig` by hand

If you want the keypair signature committed alongside the pack (instead of, or
in addition to, the CI keypair step), sign locally with the private key:

```bash
COSIGN_PASSWORD=… cosign sign-blob --yes \
  --key ~/.config/acc/signing/cosign.key \
  --output-signature packages/acc/<pkg>.accpkg.sig \
  packages/acc/<pkg>.accpkg
```

CI still adds the `.bundle` and regenerates `index.json` on tag. The
`.sig` cannot be minted keyless — keep it keypair.

## Verifying a published pack

```bash
# keyless (connected) — what a default catalog consumer does
cosign verify-blob \
  --bundle <pkg>.bundle \
  --certificate-identity-regexp '^https://github\.com/flg77/acc-ecosystem/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  <pkg>

# keypair (air-gap / pinned key, D3) — ignore Rekor for offline use
cosign verify-blob --key keys/acc-ecosystem.pub \
  --signature <pkg>.sig --insecure-ignore-tlog <pkg>
```

The air-gap path corresponds to `acc-pkg install … --offline` (a `file:`
catalog auto-enables offline), which adds `--insecure-ignore-tlog`.

## Regenerating index.json locally

```bash
python tools/gen_index.py          # rewrite ./index.json from packages/
python tools/gen_index.py --check  # CI-style staleness check (no write)
```
