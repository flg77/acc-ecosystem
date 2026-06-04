# acc-ecosystem

Public package registry for the [Agentic Cell Corpus
(ACC)](https://github.com/flg77/acc) role ecosystem.

This repo serves the canonical `@acc/*` family packs. Operators
consume it via a `catalogs.yaml` entry pointing at the GitHub Pages
URL:

```yaml
catalogs:
  - id: acc-canonical
    tier: trusted
    mode: https
    url: https://flg77.github.io/acc-ecosystem
    required_signer:
      issuer: https://token.actions.githubusercontent.com
      subject_pattern: "^https://github\.com/flg77/acc-ecosystem/"
    priority: 100
```

## Packages

| Package | Roles | Description |
|---|---|---|
| `@acc/workspace-roles` | 8 | Coding-agent + 5 variants, analyst, synthesizer |
| `@acc/research-roles` | 6 | Research planner, literature surveyor, etc. |
| `@acc/business-roles` | 25 | CEO, CTO, marketing, sales, support, ... |
| `@acc/devops-roles` | 4 | SRE, platform engineer, release engineer, ... |

Total: 43 movable roles extracted from `acc` core in Stage 2 of the
role-ecosystem strategy.

The 7 CONTROL roles (arbiter, assistant, compliance_officer,
ingester, observer, orchestrator, reviewer) stay in core.

## Index format

`index.json` is the static catalog index served at the root.  Its
schema matches `acc.pkg.catalog._fetch_index_https` (schema_version
1).  Each entry carries `name`, `version`, `tarball_sha256`,
`tarball_url`, and `signature_url`.

## Signing

Bootstrap packages are UNSIGNED.  Operators consuming the
bootstrap release must set `--allow-unsigned` (audit-logged) until
the Konflux/RHTAP pipeline lands the v1.0.1 signed release.

Once signed, every `.accpkg` carries a `cosign sign-blob` keyless
signature as a `.sig` sidecar, a Fulcio certificate as a `.pem`
sidecar, and a Rekor transparency-log entry.

## License

Apache 2.0 — see [LICENSE](LICENSE).
