# acc-ecosystem

The public package registry for the [Agentic Cell Corpus
(ACC)](https://github.com/flg77/acc) role ecosystem — the place to
**discover** ready-made agent roles and **publish your own**.

ACC core ships only the 7 CONTROL roles (`arbiter`, `assistant`,
`compliance_officer`, `ingester`, `observer`, `orchestrator`,
`reviewer`). Everything else — coding agents, researchers, business
personas, DevOps engineers — is distributed here as signed, versioned
**role packages** (`.accpkg`). You install only the roles you need, and
anyone can ship a pack.

---

## What's available

This registry serves the canonical `@acc/*` **role packs** — the 43
movable roles extracted from `acc` core during the Stage 2 role-ecosystem
split. The live set is authoritative in [`index.json`](index.json):

| Package | Roles | What's inside |
|---|---|---|
| [`@acc/workspace-roles`](packages/acc) | 8 | `coding_agent` + 5 variants (architect, dependency, implementer, reviewer, tester), `analyst`, `synthesizer` |
| [`@acc/research-roles`](packages/acc) | 6 | `research_planner`, `research_critic`, `research_strategist`, `research_economist`, `research_competitor`, `research_synthesizer` |
| [`@acc/devops-roles`](packages/acc) | 4 | `data_engineer`, `devops_engineer`, `ml_engineer`, `security_analyst` |
| [`@acc/business-roles`](packages/acc) | 25 | The frozen `1.0.x` corporate monolith (HR, sales, marketing, finance, legal, ops, IT, support) — kept so existing `^1.0` pins keep resolving |

**The corporate split.** The 25-role monolith is being replaced by
**seven per-domain packs** plus an umbrella, built from the
[spearhead](https://github.com/flg77/acc-ecosystem-spearhead) and rolling
out to this registry:

| Pack | Domain |
|---|---|
| `@acc/hr-roles` · `@acc/finance-roles` · `@acc/sales-roles` · `@acc/marketing-roles` · `@acc/legal-roles` · `@acc/support-roles` · `@acc/operations-roles` | One per knowledge domain — install only what you need |
| `@acc/business-roles@2.0.0` | **Umbrella** meta-pack — `depends_on` all seven; one `required_packages` entry pulls the closure via ACC's transitive resolver |

A vertical FSI agentset (`@acc/capital-markets-roles`, 13 roles) is also
maintained in the spearhead. Each pack is a byte-deterministic `.accpkg`
tarball carrying the role definitions, any bundled skills/MCPs,
behavioral + safety evals, and optional Cat-A/B/C policy bounds.

---

## How it works

ACC consumes this registry through its **catalog** layer. A catalog is
an entry in `catalogs.yaml` that points ACC at a registry and pins the
signer it will trust:

```yaml
# /etc/acc/catalogs.yaml  ·  ~/.acc/catalogs.yaml  ·  <workspace>/.acc/catalogs.yaml
catalogs:
  - id: acc-canonical
    tier: trusted
    mode: https
    url: https://flg77.github.io/acc-ecosystem
    required_signer:
      issuer: https://token.actions.githubusercontent.com
      subject_pattern: "^https://github\\.com/flg77/acc-ecosystem/"
    priority: 100
```

Catalogs layer **system → user → workspace**; within a layer, higher
`priority:` wins when two catalogs advertise the same `@scope/name`.

Once a catalog is declared, packages reach your agents two ways:

1. **Declared in `collective.yaml`** — list packs under
   `required_packages:`; ACC's boot-time fetch resolves, verifies, and
   unpacks them before agents spawn. The dual-source loader prefers an
   installed package over any in-tree fallback.

   ```yaml
   collective_id: my-corpus
   required_packages:
     - "@acc/workspace-roles@^1.0"
     - "@acc/research-roles@^1.0"
   ```

2. **Installed directly** — from the CLI or the **Marketplace** /
   **Catalog admin** panes in the ACC TUI / WebGUI:

   ```bash
   acc-pkg list --available
   acc-pkg install @acc/research-roles@^1.0
   ```

**Signing floor.** Every package is cosign-verified against the
catalog's `required_signer` before it installs — this is
non-negotiable. The `tier` (`trusted` / `community` / `self`) changes
only the *depth* of policy applied on top (e.g. Stage 1 Enterprise
Contract eval attestations for the trusted tier).

> **Full lifecycle** (build → publish → deploy → infuse → verify, from the
> CLI / TUI / WebGUI):
> [`acc/docs/howto-build-deploy-infuse.md`](https://github.com/flg77/acc/blob/main/docs/howto-build-deploy-infuse.md).

---

## Create your own role pack

You don't need to be on the ACC team to publish. The community path is
keyless — your signature is bound to your GitHub Actions OIDC identity,
so there are no keys to manage.

```bash
# 1. Scaffold
acc-pkg init my-coding-helper --scope @your-scope --output ./my-coding-helper

# 2. Author roles/<name>/role.yaml + write behavioral & safety evals

# 3. Build (byte-deterministic) and inspect
acc-pkg build ./my-coding-helper -o dist/my-coding-helper-0.1.0.accpkg
acc-pkg inspect dist/my-coding-helper-0.1.0.accpkg

# 4. Tag → CI signs (keyless) + publishes
git tag v0.1.0 && git push --tags
```

A package needs three things to be consumable: a schema-valid
`accpkg.yaml` manifest, a cosign signature, and an `evals/` attestation
(one behavioral + one safety eval passing against the curated-LLM
panel). The full walkthrough — from `git clone` to a signed pack in
under an hour — is in
**[`docs/CONTRIBUTING-ROLE.md`](https://github.com/flg77/acc/blob/main/docs/CONTRIBUTING-ROLE.md)**
in the core repo.

**Publisher tiers**

| Tier | Who | Policy |
|---|---|---|
| `trusted` | ACC-canonical packs (this registry) | Signature + manifest + eval attestation |
| `community` | Any OSS publisher via GitHub Actions OIDC | Signature + manifest |
| `self` | An operator's own local catalogs | Operator-defined |

---

## Index format

[`index.json`](index.json) is the static catalog index served at the
registry root. Its schema matches
`acc.pkg.catalog._fetch_index_https` (schema_version 1); each entry
carries `name`, `version`, `tarball_sha256`, `tarball_url`, and
`signature_url`.

## Signing status

* **v1.0.0** — bootstrap release, **unsigned**. Operators consuming it
  must pass `--allow-unsigned` (audit-logged).
* **v1.0.2** — **signed**. Each `.accpkg` on this Pages catalog carries a
  matching `.accpkg.sig` (served alongside the tarball, referenced by
  `signature_url` in [`index.json`](index.json)). Consume them with a
  **keypair** `required_signer`:

  ```yaml
      required_signer:
        issuer: "acc-ecosystem-keypair"      # audit label
        subject_pattern: ".*"                 # ignored in keypair mode
        key_path: /etc/acc/keys/acc-ecosystem.pub   # this repo's keys/acc-ecosystem.pub
  ```

  Verification needs the `cosign` binary on PATH (pin **cosign v2** —
  v3 changed `verify-blob` tlog defaults). The public verifier key is
  published at [`keys/acc-ecosystem.pub`](keys/acc-ecosystem.pub).

  > **Rolling out:** the keyless-OIDC publish path (Fulcio + Rekor, no key
  > custody) is being wired to deploy `.sig`/bundle to Pages — today the
  > `publish-family-packs.yml` workflow signs keyless to GitHub Releases,
  > while the Pages catalog is keypair-signed. The keypair config above is
  > the supported consumer path until the keyless-to-Pages cutover lands.

The publisher runbook for cutting a new family-pack release is
[`docs/PUBLISHING-FAMILY-PACKS.md`](https://github.com/flg77/acc/blob/main/docs/PUBLISHING-FAMILY-PACKS.md)
in the core repo.

---

## Related repositories

| Repository | What it is |
|---|---|
| [`flg77/acc`](https://github.com/flg77/acc) | The ACC runtime, operator, TUI/WebGUI, and the `acc-pkg` toolchain that consumes this registry. |
| [`flg77/acc-ecosystem`](https://github.com/flg77/acc-ecosystem) | **This repo** — the public `@acc/*` package registry. |
| [`flg77/acc-podman-desktop`](https://github.com/flg77/acc-podman-desktop) | Podman Desktop extension — run, govern, and browse roles for an ACC collective from the desktop. |
| [`flg77/acc-web-project`](https://github.com/flg77/acc-web-project) | The project website — its `/roles` marketplace surfaces packs from this registry. |

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
