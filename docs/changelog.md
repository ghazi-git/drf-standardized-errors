# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [UNRELEASED]

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
