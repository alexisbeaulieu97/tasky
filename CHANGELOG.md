# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking Changes

#### JSON Configuration Format Removed

**BREAKING**: Legacy JSON configuration format (`.tasky/config.json`) is no longer supported. All projects must use TOML format (`.tasky/config.toml`).

**Migration Steps:**

If you have an existing project with `.tasky/config.json`, convert it to TOML:

1. Rename the file:
   ```bash
   mv .tasky/config.json .tasky/config.toml
   ```

2. Convert the format from JSON to TOML syntax. Example:

   **Before (config.json):**
   ```json
   {
     "version": "1.0",
     "storage": {
       "backend": "json",
       "path": "tasks.json"
     }
   }
   ```

   **After (config.toml):**
   ```toml
   version = "1.0"

   [storage]
   backend = "json"
   path = "tasks.json"
   ```

**Rationale:**

Maintaining dual-format support added complexity to the codebase without providing significant value. TOML is more human-readable and better suited for configuration files. The migration is straightforward for the small number of configuration settings tasky requires.

---

## Historical Changes

Previous changes were tracked in git commit history and OpenSpec proposals. This CHANGELOG was introduced with the removal of JSON configuration support.
