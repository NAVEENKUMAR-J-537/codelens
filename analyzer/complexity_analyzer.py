from radon.complexity import cc_visit
from radon.visitors import Function


def analyze_complexity(file_path):

    results = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        blocks = cc_visit(source_code)

        for block in blocks:

            # Only analyze functions and methods.
            # Ignore class-level complexity blocks.
            if not isinstance(block, Function):
                continue

            complexity = block.complexity

            if complexity <= 5:
                level = "Low"

            elif complexity <= 10:
                level = "Medium"

            else:
                level = "High"

            results.append({
                "name": block.name,
                "line": block.lineno,
                "complexity": complexity,
                "level": level
            })

    except (SyntaxError, UnicodeDecodeError, OSError):
        pass

    return results