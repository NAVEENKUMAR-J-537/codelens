from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def generate_pdf_report(results):
    """
    Generate a CodeLens PDF report from analysis results.

    Returns:
        BytesIO: PDF stored in memory.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="CodeLens Analysis Report",
        author="CodeLens",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CodeLensTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#2563EB"),
    )

    subtitle_style = ParagraphStyle(
        "CodeLensSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=22,
    )

    heading_style = ParagraphStyle(
        "CodeLensHeading",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        spaceBefore=12,
        spaceAfter=10,
        textColor=colors.HexColor("#0F172A"),
    )

    normal_style = ParagraphStyle(
        "CodeLensNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )

    success_style = ParagraphStyle(
        "CodeLensSuccess",
        parent=normal_style,
        textColor=colors.HexColor("#047857"),
    )

    story = []

    # -------------------------------------------------
    # TITLE
    # -------------------------------------------------

    story.append(
        Paragraph(
            "CodeLens",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Python Codebase Analysis Report",
            subtitle_style,
        )
    )

    # -------------------------------------------------
    # PROJECT OVERVIEW
    # -------------------------------------------------

    story.append(
        Paragraph(
            "Project Overview",
            heading_style,
        )
    )

    overview_data = [
        ["Metric", "Value"],
        ["Python Files", results.get("python_files", 0)],
        ["Total Lines", results.get("total_lines", 0)],
        ["Functions", results.get("functions", 0)],
        ["Methods", results.get("methods", 0)],
        ["Async Functions", results.get("async_functions", 0)],
        ["Async Methods", results.get("async_methods", 0)],
        ["Classes", results.get("classes", 0)],
        ["Imports", results.get("imports", 0)],
        ["Decorators", results.get("decorators", 0)],
        ["Issues", len(results.get("issues", []))],
    ]

    overview_table = Table(
        overview_data,
        colWidths=[100 * mm, 55 * mm],
        repeatRows=1,
    )

    overview_table.setStyle(
        create_table_style()
    )

    story.append(overview_table)

    story.append(Spacer(1, 10 * mm))

    # -------------------------------------------------
    # CODE QUALITY
    # -------------------------------------------------

    story.append(
        Paragraph(
            "Code Quality",
            heading_style,
        )
    )

    issues = results.get("issues", [])

    if not issues:

        story.append(
            Paragraph(
                "No supported code-quality issues were detected.",
                success_style,
            )
        )

    else:

        issue_data = [
            [
                "Issue",
                "File",
                "Line",
                "Description",
            ]
        ]

        for issue in issues:

            issue_data.append(
                [
                    safe_text(issue.get("type", "")),
                    safe_text(issue.get("file", "")),
                    issue.get("line", ""),
                    safe_text(issue.get("message", "")),
                ]
            )

        issue_table = Table(
            issue_data,
            colWidths=[
                35 * mm,
                40 * mm,
                15 * mm,
                65 * mm,
            ],
            repeatRows=1,
        )

        issue_table.setStyle(
            create_table_style()
        )

        story.append(issue_table)

    story.append(
        Spacer(1, 8 * mm)
    )

    # -------------------------------------------------
    # COMPLEXITY SUMMARY
    # -------------------------------------------------

    story.append(
        Paragraph(
            "Complexity Summary",
            heading_style,
        )
    )

    complexity_summary = results.get(
        "complexity_summary",
        {},
    )

    complexity_summary_data = [
        ["Metric", "Value"],
        [
            "Average Complexity",
            complexity_summary.get(
                "average",
                0,
            ),
        ],
        [
            "Highest Complexity",
            complexity_summary.get(
                "highest",
                0,
            ),
        ],
        [
            "Most Complex",
            safe_text(
                complexity_summary.get(
                    "most_complex",
                    "N/A",
                )
            ),
        ],
        [
            "Low",
            complexity_summary.get(
                "low",
                0,
            ),
        ],
        [
            "Medium",
            complexity_summary.get(
                "medium",
                0,
            ),
        ],
        [
            "High",
            complexity_summary.get(
                "high",
                0,
            ),
        ],
    ]

    complexity_summary_table = Table(
        complexity_summary_data,
        colWidths=[
            100 * mm,
            55 * mm,
        ],
        repeatRows=1,
    )

    complexity_summary_table.setStyle(
        create_table_style()
    )

    story.append(
        complexity_summary_table
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    # -------------------------------------------------
    # COMPLEXITY DETAILS
    # -------------------------------------------------

    story.append(
        Paragraph(
            "Function & Method Complexity",
            heading_style,
        )
    )

    complexity = results.get(
        "complexity",
        [],
    )

    if complexity:

        complexity_data = [
            [
                "Name",
                "File",
                "Line",
                "Complexity",
                "Level",
            ]
        ]

        for item in complexity:

            complexity_data.append(
                [
                    safe_text(
                        item.get(
                            "name",
                            "",
                        )
                    ),
                    safe_text(
                        item.get(
                            "file",
                            "",
                        )
                    ),
                    item.get(
                        "line",
                        "",
                    ),
                    item.get(
                        "complexity",
                        "",
                    ),
                    safe_text(
                        item.get(
                            "level",
                            "",
                        )
                    ),
                ]
            )

        complexity_table = Table(
            complexity_data,
            colWidths=[
                38 * mm,
                52 * mm,
                18 * mm,
                27 * mm,
                20 * mm,
            ],
            repeatRows=1,
        )

        complexity_table.setStyle(
            create_table_style()
        )

        story.append(
            complexity_table
        )

    else:

        story.append(
            Paragraph(
                "No functions or methods were available for complexity analysis.",
                normal_style,
            )
        )

    story.append(
        Spacer(1, 8 * mm)
    )

    # -------------------------------------------------
    # DEPENDENCIES
    # -------------------------------------------------

    story.append(
        Paragraph(
            "Dependencies",
            heading_style,
        )
    )

    dependencies = results.get(
        "dependencies",
        {},
    )

    dependency_data = [
        [
            "Type",
            "Detected Dependencies",
        ],
        [
            "External Packages",
            join_items(
                dependencies.get(
                    "external",
                    [],
                )
            ),
        ],
        [
            "Standard Library",
            join_items(
                dependencies.get(
                    "standard",
                    [],
                )
            ),
        ],
        [
            "Internal Modules",
            join_items(
                dependencies.get(
                    "internal",
                    [],
                )
            ),
        ],
    ]

    dependency_table = Table(
        dependency_data,
        colWidths=[
            45 * mm,
            110 * mm,
        ],
        repeatRows=1,
    )

    dependency_table.setStyle(
        create_table_style()
    )

    story.append(
        dependency_table
    )

    # -------------------------------------------------
    # INTERNAL DEPENDENCY RELATIONSHIPS
    # -------------------------------------------------

    dependency_graph = results.get(
        "dependency_graph",
        [],
    )

    if dependency_graph:

        story.append(
            Spacer(1, 8 * mm)
        )

        story.append(
            Paragraph(
                "Internal Dependency Relationships",
                heading_style,
            )
        )

        graph_data = [
            [
                "Source",
                "Target",
            ]
        ]

        for connection in dependency_graph:

            graph_data.append(
                [
                    safe_text(
                        connection.get(
                            "source",
                            "",
                        )
                    ),
                    safe_text(
                        connection.get(
                            "target",
                            "",
                        )
                    ),
                ]
            )

        graph_table = Table(
            graph_data,
            colWidths=[
                77.5 * mm,
                77.5 * mm,
            ],
            repeatRows=1,
        )

        graph_table.setStyle(
            create_table_style()
        )

        story.append(
            graph_table
        )

    # -------------------------------------------------
    # FILE ANALYSIS
    # -------------------------------------------------

    files = results.get(
        "files",
        [],
    )

    if files:

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "File Analysis",
                heading_style,
            )
        )

        file_data = [
            [
                "File",
                "Lines",
                "Functions",
                "Methods",
                "Classes",
                "Imports",
                "Decorators",
            ]
        ]

        for file in files:

            file_data.append(
                [
                    safe_text(
                        file.get(
                            "name",
                            "",
                        )
                    ),
                    file.get(
                        "lines",
                        0,
                    ),
                    file.get(
                        "functions",
                        0,
                    ),
                    file.get(
                        "methods",
                        0,
                    ),
                    file.get(
                        "classes",
                        0,
                    ),
                    file.get(
                        "imports",
                        0,
                    ),
                    file.get(
                        "decorators",
                        0,
                    ),
                ]
            )

        file_table = Table(
            file_data,
            colWidths=[
                55 * mm,
                16 * mm,
                21 * mm,
                18 * mm,
                18 * mm,
                17 * mm,
                20 * mm,
            ],
            repeatRows=1,
        )

        file_table.setStyle(
            create_table_style()
        )

        story.append(
            file_table
        )

    # -------------------------------------------------
    # BUILD PDF
    # -------------------------------------------------

    document.build(story)

    buffer.seek(0)

    return buffer


def create_table_style():
    """
    Common styling used by report tables.
    """

    return TableStyle(
        [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1E293B"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                colors.HexColor("#F8FAFC"),
            ),
            (
                "TEXTCOLOR",
                (0, 1),
                (-1, -1),
                colors.HexColor("#0F172A"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ]
    )


def safe_text(value):
    """
    Convert values into safe display strings.
    """

    if value is None:
        return ""

    return str(value)


def join_items(items):
    """
    Convert a dependency list into readable text.
    """

    if not items:
        return "None detected"

    return ", ".join(
        str(item)
        for item in items
    )