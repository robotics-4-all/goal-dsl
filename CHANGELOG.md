# Telos Changelog

All _notable_ changes to this project will be documented in this file.

The format is based on _[Keep a Changelog][keepachangelog]_, and this project
adheres to _[Semantic Versioning][semver]_.

Backward incompatible changes are marked with **(BIC)**.

## [0.5.0] - 2026-02-26

### Changed

- **(BIC)** Renamed project from GoalDSL to **Telos**
- **(BIC)** Python package: `goal_dsl` → `telos`
- **(BIC)** CLI command: `goaldsl` → `telos`
- **(BIC)** File extension: `.goal` → `.telos`
- **(BIC)** Environment variables: `GOALDSL_*` → `TELOS_*`
- **(BIC)** textX language name: `goal_dsl` → `telos`
- **(BIC)** Root grammar rule: `GoalDSLModel` → `TelosModel`
- Docker service name: `goaldsl` → `telos`
- Version bumped to 0.5.0

## [Unreleased]

[Unreleased]: https://github.com/robotics-4-all/goal-dsl/commits/devel
[0.5.0]: https://github.com/robotics-4-all/goal-dsl/releases/tag/v0.5.0


[keepachangelog]: https://keepachangelog.com/
[semver]: https://semver.org/spec/v2.0.0.html
[textXDocs]: http://textx.github.io/textX/latest/