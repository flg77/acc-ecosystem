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

This registry serves the canonical `@acc/*` **role packs** — movable
roles extracted from `acc` core during the Stage 2 role-ecosystem split.

**Foundational families:**

| Package | Roles | What's inside |
|---|---|---|
| [`@acc/workspace-roles`](packages/acc) | 8 | `coding_agent` + 5 variants (architect, dependency, implementer, reviewer, tester), `analyst`, `synthesizer` |
| [`@acc/research-roles`](packages/acc) | 6 | `research_planner`, `research_critic`, `research_strategist`, `research_economist`, `research_competitor`, `research_synthesizer` |
| [`@acc/devops-roles`](packages/acc) | 4 | `data_engineer`, `devops_engineer`, `ml_engineer`, `security_analyst` |

**Corporate domain packs** (the former `@acc/business-roles` monolith,
now split so you install only the domains you need):

| Package | Roles | What's inside |
|---|---|---|
| [`@acc/hr-roles`](packages/acc) | 3 | hr_business_partner, learning_development_specialist, recruiter |
| [`@acc/finance-roles`](packages/acc) | 2 | financial_analyst, fpa_analyst |
| [`@acc/sales-roles`](packages/acc) | 7 | account_executive, sales_development_rep, sales_engineer, key_account_manager, inside_sales_rep, sales_operations_manager, revenue_operations_analyst |
| [`@acc/marketing-roles`](packages/acc) | 5 | content_marketer, demand_generation_specialist, marketing_analyst, product_marketer, brand_manager |
| [`@acc/legal-roles`](packages/acc) | 2 | contract_analyst, risk_compliance_analyst |
| [`@acc/support-roles`](packages/acc) | 3 | customer_success_manager, customer_support_agent, technical_support_specialist |
| [`@acc/operations-roles`](packages/acc) | 7 | business_analyst, operations_analyst, procurement_specialist, project_manager, product_manager, it_operations_specialist, it_support_specialist |
| [`@acc/business-roles`](packages/acc) `@2.0.0` | — | **Umbrella** — `depends_on` all seven corporate packs above; install one entry, get the whole suite. |

> **Upgrading from the monolith?** The frozen `@acc/business-roles@1.0.x`
> (25-role monolith) stays published, so existing `@acc/business-roles@^1.0`
> pins keep resolving unchanged. Pin `@acc/business-roles@^2.0` (the
> umbrella) to pull all seven domain packs via ACC's transitive resolver,
> or pick individual `@acc/<domain>-roles` packs. Four roles are new in the
> split: `key_account_manager`, `inside_sales_rep`, `sales_operations_manager`,
> `brand_manager`.

Each pack is a byte-deterministic `.accpkg` tarball carrying the role
definitions, any bundled skills/MCPs, behavioral + safety evals, and
optional Cat-A/B/C policy bounds. The current set of versions is listed
in [`index.json`](index.json).

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
* **v1.0.2** — first **signed** release. Each `.accpkg` is signed with
  keyless `cosign sign-blob` (Fulcio certificate + Rekor transparency
  log) via the repo's GitHub Actions OIDC identity; signatures are
  attached to the matching GitHub Release.

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
