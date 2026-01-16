# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.14.1] - 2026-01-16

### Fixed

- Fixed rich_click behavior.

## [0.14.0] - 2026-01-16

### Added

- Improved exception handling.
- Improved type checking.

### Changed

- Access Canvas API directly without requiring the canvasapi package.
- Use Pydantic for validating all models.

### Fixed

- Fix crash when course name is missing (hopefully).

## [0.13.1] - 2025-11-09

### Fixed

- Use raw string literal for regular expressions.

## [0.13.0] - 2025-11-08

### Changed

- Use uv instead of Poetry.
- Use platformdirs instead of the deprecated appdirs.

## [0.12.0] - 2024-11-22

### Added

- Added time passed deadline for submissions.
- Added all submission attempts.
- Added grade and score for submissions.
- Added submission comments.

### Changed

- Use Pydantic for validating responses from the Canvas API
- Communicate directly with the Canvas API, without going through the canvasapi package for some tasks. In the future, the canvasapi dependency will be dropped.

## [0.11.0] - 2024-10-31

### Added

- When listing all students in a course, optionally include the test student.

## [0.10.3] - 2024-08-30

### Added

- When running `canvas courses list`, list aliases which don't have access to a course.

### Fixed

- Don't crash when listing a course for which you no longer have access.
