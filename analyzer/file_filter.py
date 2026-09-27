from pathlib import Path


# Directories that normally do not contain
# the user's actual project source code.
IGNORED_DIRECTORIES = {
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".git",
    ".github",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "site-packages"
}


def should_ignore_file(file_path, project_path):

    file_path = Path(file_path)
    project_path = Path(project_path)

    relative_path = file_path.relative_to(
        project_path
    )

    # We check only directory parts,
    # not the filename itself.
    for part in relative_path.parts[:-1]:

        part_lower = part.lower()

        if part_lower in IGNORED_DIRECTORIES:
            return True

        # Handles directories such as:
        # package_name.egg-info
        if part_lower.endswith(".egg-info"):
            return True

    return False


def get_python_files(project_path):

    project_path = Path(project_path)

    python_files = []

    for file_path in project_path.rglob("*.py"):

        if should_ignore_file(
            file_path,
            project_path
        ):
            continue

        python_files.append(
            file_path
        )

    return python_files