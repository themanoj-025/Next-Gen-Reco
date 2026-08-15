# SecurityAndCompliance — MovieLens AI: Security

| Field | Value |
| --- | --- |
| Version | v0.1 |
| Last Updated | 2026-08-06 |
| Owner | Security Engineer |
| Status | In Review |

---

## 1. Threat Model (STRIDE)

| Threat | Surface | Impact | Mitigation |
| --- | --- | --- | --- |
| Tampering | Search input | Odd results | Input validation |
| DoS | Heavy queries | Slow app | Caching, limits |
| Info disclosure | User session data | Privacy | Session-scoped state |
| (others) | N/A | — | Local single-user tool |

## 2. Auth / Authorization

- No accounts in v1; local dashboard state.

## 3. Data Classification

| Data | Class | Handling |
| --- | --- | --- |
| Movie data | public | — |
| User watchlist (session) | personal | session-scoped |
| Model artifacts | internal | repo |

## 4. Encryption

- In transit: TLS on Streamlit Cloud.

## 5. Compliance Checklist

- [ ] No PII collected beyond optional session data
- [ ] MovieLens dataset license respected (research use)
- [ ] Dependency scans

## 6. Incident Response Plan (outline)

1. Detect: hosting alerts.
2. Triage.
3. Contain: revert/deploy.
4. Remediate.
5. Recover.
6. Postmortem.

## 7. Related Documents

| Document | Relationship |
| --- | --- |
| [Rules.md](../project/Rules.md) | Security rules |
| [Schema.md](Schema.md) | Sensitive map |
| [TechSpec.md](TechSpec.md) | NFRs |
| [PRD.md](../product/PRD.md) | Goals |
| [AppFlow.md](../design/AppFlow.md) | Flows |
| [Design.md](../design/Design.md) | Design |
| [ImplementationPlan.md](../project/ImplementationPlan.md) | Tasks |
| [Tracker.md](../project/Tracker.md) | Status |
| [Testing.md](Testing.md) | Security tests |
| [Deployment.md](Deployment.md) | Deploy |
| [Glossary.md](../reference/Glossary.md) | Vocabulary |
| [RiskRegister.md](../project/RiskRegister.md) | Risks |
