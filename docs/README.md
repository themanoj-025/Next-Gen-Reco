# MovieLens AI (Next-Gen-Reco) — Documentation Index

Single home for all Next-Gen-Reco documentation. Next-Gen-Reco is a movie
rating & recommendation app (MovieLens AI) with ML-driven recommendations.

**Start here:** [architecture.md](architecture.md) (system map) →
[folder_structure.md](folder_structure.md) (repo tree) →
[technical/TechSpec.md](technical/TechSpec.md) (build details).

## Structure

```
docs/
├── README.md                      ← this index
├── architecture.md                system architecture
├── folder_structure.md            repository + docs tree
├── module_dependency.md           dependency graph
├── package_overview.md            module inventory
├── startup_flow.md                boot + recommendation flow
├── community/
│   ├── CHANGELOG.md               changelog
│   ├── CODE_OF_CONDUCT.md         code of conduct
│   ├── CONTRIBUTING.md            contribution guide
│   ├── SECURITY.md                security policy
│   └── SUPPORT.md                 support channels
├── design/
│   ├── AppFlow.md                 app screens / states / flows
│   └── Design.md                  design decisions
├── product/
│   └── PRD.md                     product requirements
├── project/
│   ├── analysis_report.md         repo inventory & classification
│   ├── ImplementationPlan.md      implementation plan
│   ├── RiskRegister.md            risks & mitigations
│   ├── Rules.md                   engineering rules
│   └── Tracker.md                 status tracker
├── reference/
│   └── Glossary.md                terminology
├── technical/
│   ├── API.md                     endpoint reference
│   ├── Deployment.md              deployment guide
│   ├── Schema.md                  data model
│   ├── SecurityAndCompliance.md   security baseline
│   ├── TechSpec.md                technical spec
│   └── Testing.md                 test strategy
├── migration/
│   ├── migration_summary.md       modernization record
│   ├── old_tree_to_new_tree.md    restructure before/after
│   └── file_move_ledger.md        file-move ledger
└── audit/
    ├── cleanup-audit-2026-08-13.md  previous cleanup audit
    └── cleanup-audit-2026-08-15.md  docs de-LLM-ification audit
```

## Guidance

| You want... | Read |
|---|---|
| How the app works end-to-end | [architecture.md](architecture.md) |
| Where everything lives | [folder_structure.md](folder_structure.md) |
| API surface | [technical/API.md](technical/API.md) |
| Deployment | [technical/Deployment.md](technical/Deployment.md) |
| What's shipped / next | [project/Tracker.md](project/Tracker.md) |
| Risks & follow-ups | [project/RiskRegister.md](project/RiskRegister.md) |
