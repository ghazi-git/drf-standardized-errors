import pathlib
from argparse import ArgumentParser
from datetime import date

CHANGELOG_RELATIVE_PATH = "docs/changelog.md"
CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
CHANGELOG_ABS_PATH = CURRENT_DIR.parent / CHANGELOG_RELATIVE_PATH
UNRELEASED_LINE = "## [UNRELEASED]"
NEW_VERSION_LINE_TEMPLATE = "## [{version}] - {date}\n"


def main(version):
    lines = get_changelog_file_content()
    unreleased_line_number = find_unreleased_line_number(lines)
    lines = add_new_version_to_changelog(lines, unreleased_line_number, version)
    update_changelog_file(lines)


def get_changelog_file_content():
    with open(CHANGELOG_ABS_PATH, encoding="utf-8") as f:
        return f.readlines()


def find_unreleased_line_number(lines):
    unreleased_line_number = None
    for i, line in enumerate(lines):
        if line.strip().lower() == UNRELEASED_LINE.lower():
            unreleased_line_number = i
            break

    if unreleased_line_number is None:
        # Abort the release process as we're not able to update the changelog.
        # If, for some reason, there is no need to update the changelog, comment
        # the step to update the changelog in pyproject.toml
        raise ChangelogUpdateError(
            f"Unable to find a line with the text '{UNRELEASED_LINE}' when "
            f"trying to update the changelog at '{CHANGELOG_RELATIVE_PATH}'."
        )
    return unreleased_line_number


def add_new_version_to_changelog(lines, unreleased_line_number, version):
    new_version_line = NEW_VERSION_LINE_TEMPLATE.format(
        version=version, date=date.today()
    )
    return (
        lines[: unreleased_line_number + 1]
        + ["\n", new_version_line]
        + lines[unreleased_line_number + 1 :]
    )


def update_changelog_file(lines):
    with open(CHANGELOG_ABS_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


class ChangelogUpdateError(Exception):
    """Unable to update the changelog with the new version"""


if __name__ == "__main__":
    parser = ArgumentParser(
        description=(
            "Replace UNRELEASED with the new version and current date and add "
            "a new unreleased section to the changelog."
        )
    )
    parser.add_argument(
        "-n",
        "--new-version",
        dest="version",
        help="The new version to be released",
        metavar="NEW_VERSION",
    )
    args = parser.parse_args()

    main(args.version)
