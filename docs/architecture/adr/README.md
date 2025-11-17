# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting significant design decisions made in the Tasky project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help developers understand why the system is built the way it is, making onboarding and maintenance easier.

## Format

We use a lightweight ADR format based on Michael Nygard's template. Each ADR includes:

- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: What issue are we addressing?
- **Decision**: What are we doing about it?
- **Consequences**: What are the positive and negative impacts?
- **Alternatives**: What other options did we consider?

See `0000-template.md` for the full template.

## Index of ADRs

### Active Decisions

- [ADR-001: Backend Registry Pattern with Self-Registration](0001-backend-registry-pattern.md)  
  **Status**: Accepted  
  **Summary**: How storage backends register themselves with the settings layer without tight coupling.

- [ADR-002: Error Handling Strategy - Domain vs Infrastructure Errors](0002-error-handling-strategy.md)  
  **Status**: Accepted  
  **Summary**: Protocol-based error decoupling to maintain clean architecture boundaries.

- [ADR-003: Configuration Hierarchy and Settings Precedence](0003-configuration-hierarchy.md)  
  **Status**: Accepted  
  **Summary**: How configuration sources (CLI args, env vars, config files) are prioritized.

- [ADR-004: Project Registry Storage Format](0004-project-registry-storage.md)  
  **Status**: Accepted  
  **Summary**: Why we use JSON instead of SQLite for the global project registry.

### Deprecated/Superseded

None yet.

## Contributing

When making a significant architectural decision:

1. Copy `0000-template.md` to a new file: `000X-short-title.md`
2. Fill in the template with your decision context, options, and rationale
3. Submit for review as part of your PR
4. Update this README with an entry in the index

## References

- [Michael Nygard's ADR template](https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md)
- [ADR GitHub Organization](https://adr.github.io/)
