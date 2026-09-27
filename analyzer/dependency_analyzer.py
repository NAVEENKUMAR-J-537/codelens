import ast
import sys
from pathlib import Path

from analyzer.file_filter import get_python_files


def get_project_modules(project_path):

    project_path = Path(project_path)

    modules = set()

    # Get only useful project Python files.
    python_files = get_python_files(
        project_path
    )

    for file_path in python_files:

        relative_path = file_path.relative_to(
            project_path
        )

        # Remove .py extension
        parts = list(
            relative_path
            .with_suffix("")
            .parts
        )

        # __init__.py represents its package
        if parts[-1] == "__init__":
            parts = parts[:-1]

        if not parts:
            continue

        # Example:
        # utils/helper.py
        # ->
        # utils.helper

        modules.add(
            ".".join(parts)
        )

        # Also store root module.
        #
        # utils.helper
        # ->
        # utils

        modules.add(
            parts[0]
        )

    return modules


def analyze_dependencies(
    file_path,
    project_modules
):

    dependencies = {
        "standard": set(),
        "external": set(),
        "internal": set()
    }

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            source_code = file.read()

        tree = ast.parse(
            source_code
        )

        for node in ast.walk(tree):

            # Example:
            #
            # import os
            # import pandas as pd

            if isinstance(
                node,
                ast.Import
            ):

                for alias in node.names:

                    module_name = (
                        alias.name
                    )

                    classify_dependency(
                        module_name,
                        project_modules,
                        dependencies
                    )

            # Example:
            #
            # from flask import Flask
            # from database import Database

            elif isinstance(
                node,
                ast.ImportFrom
            ):

                if node.module:

                    module_name = (
                        node.module
                    )

                    classify_dependency(
                        module_name,
                        project_modules,
                        dependencies
                    )

        return dependencies

    except (
        SyntaxError,
        UnicodeDecodeError,
        OSError
    ):

        return dependencies


def classify_dependency(
    module_name,
    project_modules,
    dependencies
):

    root_module = (
        module_name
        .split(".")[0]
    )

    # -----------------------------------
    # STANDARD PYTHON LIBRARY
    # -----------------------------------

    if (
        root_module
        in sys.stdlib_module_names
    ):

        dependencies[
            "standard"
        ].add(
            root_module
        )

    # -----------------------------------
    # INTERNAL PROJECT MODULE
    # -----------------------------------

    elif (
        module_name
        in project_modules

        or

        root_module
        in project_modules
    ):

        dependencies[
            "internal"
        ].add(
            module_name
        )

    # -----------------------------------
    # THIRD-PARTY PACKAGE
    # -----------------------------------

    else:

        dependencies[
            "external"
        ].add(
            root_module
        )


def build_dependency_graph(
    project_path
):

    project_path = Path(
        project_path
    )

    graph = []

    # IMPORTANT:
    #
    # Use the exact same filtered list
    # used by the scanner.

    python_files = get_python_files(
        project_path
    )

    # -----------------------------------
    # CREATE MODULE -> FILE MAPPING
    # -----------------------------------

    module_to_file = {}

    for file_path in python_files:

        relative_path = (
            file_path.relative_to(
                project_path
            )
        )

        parts = list(
            relative_path
            .with_suffix("")
            .parts
        )

        if parts[-1] == "__init__":
            continue

        module_name = ".".join(
            parts
        )

        module_to_file[
            module_name
        ] = relative_path.as_posix()

    # -----------------------------------
    # ANALYZE IMPORTS IN EVERY FILE
    # -----------------------------------

    for file_path in python_files:

        relative_source = (
            file_path.relative_to(
                project_path
            )
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                source_code = file.read()

            tree = ast.parse(
                source_code
            )

            for node in ast.walk(tree):

                imported_modules = []

                # ---------------------------
                # import database
                # ---------------------------

                if isinstance(
                    node,
                    ast.Import
                ):

                    for alias in node.names:

                        imported_modules.append(
                            alias.name
                        )

                # ---------------------------
                # from database import Database
                # ---------------------------

                elif isinstance(
                    node,
                    ast.ImportFrom
                ):

                    if node.module:

                        imported_modules.append(
                            node.module
                        )

                # ---------------------------
                # MATCH IMPORT TO PROJECT FILE
                # ---------------------------

                for module_name in imported_modules:

                    if (
                        module_name
                        in module_to_file
                    ):

                        target_file = (
                            module_to_file[
                                module_name
                            ]
                        )

                        graph.append({
                            "source":
                                relative_source
                                .as_posix(),

                            "target":
                                target_file
                        })

        except (
            SyntaxError,
            UnicodeDecodeError,
            OSError
        ):

            continue

    return graph