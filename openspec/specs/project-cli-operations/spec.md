# project-cli-operations Specification

## Purpose
TBD - created by archiving change add-configurable-storage-backends. Update Purpose after archive.
## Requirements
### Requirement: Display project configuration

The system SHALL provide a command to display the current project configuration.

#### Scenario: Show project info

```gherkin
Given a project with config:
  """
  {
    "version": "1.0",
    "storage": {
      "backend": "json",
      "path": "tasks.json"
    },
    "created_at": "2025-11-11T10:00:00Z"
  }
  """
When I run "tasky project info"
Then the CLI outputs:
  """
  Project Configuration
  ---------------------
  Location: /home/user/myproject/.tasky
  Backend: json
  Storage: tasks.json
  Created: 2025-11-11 10:00:00+00:00
  """
```

#### Scenario: Show info when no project found

```gherkin
Given no ".tasky/config.json" exists
When I run "tasky project info"
Then it exits with error code 1
And the error message includes "No project found"
And the error message suggests "Run 'tasky project init' first"
```

---

### Requirement: Backend validation during init

The system SHALL validate backend availability before creating configuration.

#### Scenario: List available backends in help text

```gherkin
When I run "tasky project init --help"
Then the help text includes:
  """
  --backend, -b TEXT  Storage backend (default: json)
                      Available: json, sqlite
  """
```

#### Scenario: Validate backend is registered

```gherkin
Given only "json" backend is registered
When I run "tasky project init --backend json"
Then the command succeeds
When I run "tasky project init --backend fake"
Then the command fails with "Backend 'fake' not found"
```

---

