# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [UNRELEASED]
### Fixed
- generate the mapping for discriminator fields properly instead of showing a "null" value in the generated schema (#12).

## [0.12.0] - 2022-08-27
### Added
- add support for automatically generating error responses schema with [drf-spectacular](https://github.com/tfranzel/drf-spectacular).
Check out the [corresponding documentation page](https://drf-standardized-errors.readthedocs.io/en/latest/openapi.html)
to know more about the integration with drf-spectacular.
- add support for django 4.1

## [0.11.0] - 2022-06-24
### Changed (Backward-incompatible)
- Removed all imports from `drf_standardized_errors.__init__.py`. This avoids facing the `AppRegistryNotReady` error
in certain situations (fixes #7). This change **only affects where functions/classes are imported from**, there are
**no changes to how they work**. To upgrade to this version, you need to:
  - Update the `"EXCEPTION_HANDLER"` setting in `REST_FRAMEWORK` to `"drf_standardized_errors.handler.exception_handler"`.
  - If you imported the exception handler directly, make sure the import looks like this
  `from drf_standardized_errors.handler import exception_handler`.
  - If you imported the exception handler class, make sure the import looks like this
  `from drf_standardized_errors.handler import ExceptionHandler`.
  - If you imported the exception formatter class, make sure the import looks like this
  `from drf_standardized_errors.formatter import ExceptionFormatter`.

## [0.10.2] - 2022-05-08
### Fixed
- disable tag creation by the "create GitHub release" action since it is already created by tbump

## [0.10.1] - 2022-05-08
### Fixed
- add write permission to create release action, so it can push release notes to GitHub
- fix license badge link so it works on PyPI

## [0.10.0] - 2022-05-08
### Added

- Build the documentation automatically on every commit to the main branch. The docs are
[hosted on readthedocs](https://drf-standardized-errors.readthedocs.io/en/latest/).
- Add package metadata
- add a GitHub workflow to create a GitHub release when a new tag is pushed
- add a GitHub workflow to run tests on every push and pull request
- add test coverage

## [0.9.0] - 2022-05-07
### Added

- Common error response format for DRF-based APIs
- Easily customize the error response format.
- Handle error responses for list serializers and nested serializers. 
- Add documentation
- Add tests
- Automate release steps
