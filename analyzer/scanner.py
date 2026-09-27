from pathlib import Path

from analyzer.code_analyzer import analyze_python_file
from analyzer.complexity_analyzer import analyze_complexity
from analyzer.dependency_analyzer import (
    get_project_modules,
    analyze_dependencies,
    build_dependency_graph,
)
from analyzer.file_filter import get_python_files

def scan_project(project_path):

    # Convert project path into a Path object
    project_path = Path(project_path)

    # Find all Python files inside the project
    # python_files = list(project_path.rglob("*.py"))
    python_files = get_python_files(project_path)

    # Find modules that belong to this project
    project_modules = get_project_modules(project_path)

    # Overall project results
    results = {
        "python_files": len(python_files),
        "total_lines": 0,
        "functions": 0,
        "methods": 0,
        "async_functions": 0,
        "async_methods": 0,
        "classes": 0,
        "imports": 0,
        "decorators": 0,
        "issues": [],
        "complexity": [],
        
        "complexity_summary": {
        "average": 0,
        "highest": 0,
        "most_complex": "N/A",
        "low": 0,
        "medium": 0,
        "high": 0
    },
        "dependencies": {"standard": set(), "external": set(), "internal": set()},
        "dependency_graph": [],
        "files": [],
    }

    # Analyze every Python file
    for file_path in python_files:

        # -----------------------------------
        # 1. BASIC CODE ANALYSIS
        # -----------------------------------

        file_results = analyze_python_file(file_path)

        # Add values to project-wide totals
        results["total_lines"] += file_results["lines"]
        results["functions"] += file_results["functions"]
        results["methods"] += file_results["methods"]
        results["async_functions"] += file_results["async_functions"]
        results["async_methods"] += file_results["async_methods"]
        results["classes"] += file_results["classes"]
        results["imports"] += file_results["imports"]
        results["decorators"] += file_results["decorators"]

        # Get relative filename
        relative_path = file_path.relative_to(project_path)
        relative_path_display = relative_path.as_posix()

        # -----------------------------------
        # 2. CODE QUALITY ISSUES
        # -----------------------------------

        for issue in file_results["issues"]:

            # Add filename to detected issue
            issue["file"] = relative_path_display

            # Add issue to overall project results
            results["issues"].append(issue)

        # -----------------------------------
        # 3. COMPLEXITY ANALYSIS
        # -----------------------------------

        complexity_results = analyze_complexity(file_path)

        for item in complexity_results:

            # Add filename to complexity result
            item["file"] = relative_path_display

            # Add to overall complexity results
            results["complexity"].append(item)

        # -----------------------------------
        # 4. DEPENDENCY ANALYSIS
        # -----------------------------------

        dependency_results = analyze_dependencies(file_path, project_modules)

        results["dependencies"]["standard"].update(dependency_results["standard"])

        results["dependencies"]["external"].update(dependency_results["external"])

        results["dependencies"]["internal"].update(dependency_results["internal"])

        # -----------------------------------
        # 5. PER-FILE INFORMATION
        # -----------------------------------

        results["files"].append(
            {
                "name": relative_path_display,
                "lines": file_results["lines"],
                "functions": file_results["functions"],
                "methods": file_results["methods"],
                "async_functions": file_results["async_functions"],
                "async_methods": file_results["async_methods"],
                "classes": file_results["classes"],
                "imports": file_results["imports"],
                "decorators": file_results["decorators"],
            }
        )
    # -----------------------------------
    # COMPLEXITY SUMMARY
    # -----------------------------------

    if results["complexity"]:

        total_complexity = sum(
            item["complexity"]
            for item in results["complexity"]
        )

        results["complexity_summary"]["average"] = round(
            total_complexity / len(results["complexity"]),
            2
        )

        most_complex_item = max(
            results["complexity"],
            key=lambda item: item["complexity"]
        )

        results["complexity_summary"]["highest"] = (
            most_complex_item["complexity"]
        )

        results["complexity_summary"]["most_complex"] = (
            most_complex_item["name"]
        )

        for item in results["complexity"]:

            level = item["level"].lower()

            if level == "low":
                results["complexity_summary"]["low"] += 1

            elif level == "medium":
                results["complexity_summary"]["medium"] += 1

            elif level == "high":
                results["complexity_summary"]["high"] += 1
    # -----------------------------------
    # BUILD INTERNAL DEPENDENCY GRAPH
    # -----------------------------------

    results["dependency_graph"] = build_dependency_graph(project_path)

    # -----------------------------------
    # FINAL CLEANUP
    # -----------------------------------

    # Convert sets into sorted lists
    # so Jinja can display them easily
    results["dependencies"]["standard"] = sorted(results["dependencies"]["standard"])

    results["dependencies"]["external"] = sorted(results["dependencies"]["external"])

    results["dependencies"]["internal"] = sorted(results["dependencies"]["internal"])

    return results
