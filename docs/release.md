# Release

## Automated Release
The release is automated using [tbump](https://github.com/dmerejkowsky/tbump). So, to create a new release:
- run `pip install .[release]` (preferably inside a virtualenv) 
- run `tbump <new_version>` (e.g. `tbump 0.6.0`).

That's it, the package should then be available on PyPI.

### Next in automation
- the docs should be built automatically on every release. [This](https://blog.readthedocs.com/automation-rules/)
should help.
- Readthedocs has [webhooks](https://docs.readthedocs.io/en/stable/build-notifications.html#build-status-webhooks)
that can be used as the trigger for creating a release on GitHub. Then, we need some way to use GitHub API
to actually create the release with a link to the changelog (or a copy of it). A candidate for taking care
of this is a [GitHub action](https://github.com/softprops/action-gh-release).

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
