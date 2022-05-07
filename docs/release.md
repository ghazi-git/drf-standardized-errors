# Release

## Automated Release
The release is automated using [tbump](https://github.com/dmerejkowsky/tbump). So, to create a new release:
- run `pip install .[release]` (preferably inside a virtualenv) 
- run `tbump <new_version>` (e.g. `tbump 0.6.0`).

That's it, the package should then be available on [PyPI](https://pypi.org/project/drf-standardized-errors/).

As part of the previous step, a GitHub release is created since a new tag is pushed. That's automated
[using GitHub actions](https://github.com/ghazi-git/drf-standardized-errors/actions/workflows/github_release.yml).

For the documentation, it is built automatically on every commit to the main branch. It can be found
[here](https://drf-standardized-errors.readthedocs.io/en/latest/).

## Manual Release Steps

This is kept as docs in case the release flow needs to change or someone new is trying to understand what's going on
to make some change or improve it. 

- `pip install .[release]`
- update the changelog:
  - replace unreleased with the current version and date
  - create a new unreleased section at the top.
- update the version in `drf_standardized_errors.__init__.__version__`
- commit changes
- create a tag with the new version as `v{version}`
- push changes
- publish release to pypi: the command `flit publish` takes care of that.
- build the docs
- create a new release on GitHub.
