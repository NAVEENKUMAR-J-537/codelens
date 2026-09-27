from flask import (
    Flask,
    render_template,
    request,
    send_file,
    jsonify,
    abort,
)

from pathlib import Path
import copy
import shutil
import time
import uuid
import zipfile

from analyzer.scanner import scan_project
from analyzer.file_filter import should_ignore_file
from report_generator import generate_pdf_report


app = Flask(__name__)


# =================================================
# CONFIGURATION
# =================================================

UPLOAD_FOLDER = Path("uploads")

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_EXTRACTED_SIZE = 30 * 1024 * 1024

MAX_PYTHON_FILES = 300
MAX_ZIP_ENTRIES = 2000

REPORT_EXPIRY_SECONDS = 30 * 60


# Flask itself rejects requests larger than 10 MB.
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE


# =================================================
# TEMPORARY REPORT STORAGE
# =================================================

analysis_reports = {}


# =================================================
# HOME
# =================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =================================================
# ANALYZE
# =================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    cleanup_expired_reports()

    uploaded_file = request.files.get(
        "project"
    )

    if (
        not uploaded_file
        or uploaded_file.filename == ""
    ):
        return error_response(
            "No file selected.",
            400
        )

    original_filename = (
        uploaded_file.filename
    )

    filename = (
        original_filename.lower()
    )

    if not (
        filename.endswith(".zip")
        or filename.endswith(".py")
    ):
        return error_response(
            "Only .py and .zip files are supported.",
            400
        )

    project_id = str(
        uuid.uuid4()
    )

    project_folder = (
        UPLOAD_FOLDER
        / project_id
    )

    project_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        # =========================================
        # ZIP PROJECT
        # =========================================

        if filename.endswith(".zip"):

            zip_path = (
                project_folder
                / "project.zip"
            )

            uploaded_file.save(
                zip_path
            )

            with zipfile.ZipFile(
                zip_path,
                "r"
            ) as zip_file:

                validate_and_extract_zip(
                    zip_file,
                    project_folder
                )

            # Remove the original ZIP before scanning.
            zip_path.unlink(
                missing_ok=True
            )

        # =========================================
        # SINGLE PYTHON FILE
        # =========================================

        else:

            safe_filename = Path(
                original_filename
            ).name

            python_path = (
                project_folder
                / safe_filename
            )

            uploaded_file.save(
                python_path
            )

        # =========================================
        # CHECK USEFUL PYTHON FILES
        # =========================================

        python_files = get_useful_python_files(
            project_folder
        )

        if not python_files:

            return error_response(
                "No Python files were found in this project.",
                400
            )

        if len(python_files) > MAX_PYTHON_FILES:

            return error_response(
                (
                    "This project contains too many Python files. "
                    f"Maximum supported: {MAX_PYTHON_FILES}."
                ),
                400
            )

        # =========================================
        # ANALYZE
        # =========================================

        results = scan_project(
            project_folder
        )

        report_id = str(
            uuid.uuid4()
        )

        analysis_reports[
            report_id
        ] = {
            "created_at": time.time(),
            "results": copy.deepcopy(
                results
            )
        }

        return render_template(
            "results.html",
            results=results,
            report_id=report_id
        )

    except zipfile.BadZipFile:

        return error_response(
            "The uploaded ZIP file is invalid or corrupted.",
            400
        )

    except ValueError as error:

        return error_response(
            str(error),
            400
        )

    finally:

        shutil.rmtree(
            project_folder,
            ignore_errors=True
        )


# =================================================
# PDF REPORT
# =================================================

@app.route(
    "/report/<report_id>/pdf"
)
def download_pdf_report(
    report_id
):

    cleanup_expired_reports()

    report = analysis_reports.get(
        report_id
    )

    if report is None:
        abort(404)

    pdf_buffer = generate_pdf_report(
        report["results"]
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=(
            "codelens_analysis_report.pdf"
        )
    )


# =================================================
# JSON REPORT
# =================================================

@app.route(
    "/report/<report_id>/json"
)
def download_json_report(
    report_id
):

    cleanup_expired_reports()

    report = analysis_reports.get(
        report_id
    )

    if report is None:
        abort(404)

    response = jsonify(
        report["results"]
    )

    response.headers[
        "Content-Disposition"
    ] = (
        "attachment; "
        "filename=codelens_analysis_report.json"
    )

    return response


# =================================================
# ZIP VALIDATION + EXTRACTION
# =================================================

def validate_and_extract_zip(
    zip_file,
    destination
):

    destination = (
        Path(destination).resolve()
    )

    members = (
        zip_file.infolist()
    )

    # -----------------------------------------
    # TOO MANY ZIP ENTRIES
    # -----------------------------------------

    if len(members) > MAX_ZIP_ENTRIES:

        raise ValueError(
            (
                "ZIP contains too many files or folders. "
                f"Maximum supported: {MAX_ZIP_ENTRIES} entries."
            )
        )

    total_extracted_size = 0

    files_to_extract = []

    # -----------------------------------------
    # VALIDATE EVERY ENTRY
    # -----------------------------------------

    for member in members:

        # Encrypted ZIP entry
        if member.flag_bits & 0x1:

            raise ValueError(
                "Encrypted ZIP files are not supported."
            )

        member_path = (
            destination
            / member.filename
        ).resolve()

        # Prevent:
        #
        # ../../outside.py

        try:

            member_path.relative_to(
                destination
            )

        except ValueError:

            raise ValueError(
                "Unsafe path detected inside ZIP file."
            )

        # Directories themselves don't need
        # extraction-size accounting.

        if member.is_dir():
            continue

        # -----------------------------------------
        # IGNORE USELESS DIRECTORIES
        # -----------------------------------------

        if should_ignore_file(
            member_path,
            destination
        ):
            continue

        total_extracted_size += (
            member.file_size
        )

        if (
            total_extracted_size
            > MAX_EXTRACTED_SIZE
        ):

            raise ValueError(
                (
                    "ZIP contents are too large. "
                    "Maximum extracted size is 30 MB."
                )
            )

        files_to_extract.append(
            member
        )

    # -----------------------------------------
    # EXTRACT ONLY ACCEPTED FILES
    # -----------------------------------------

    for member in files_to_extract:

        zip_file.extract(
            member,
            destination
        )


# =================================================
# FIND USEFUL PYTHON FILES
# =================================================

def get_useful_python_files(
    project_folder
):

    project_folder = Path(
        project_folder
    )

    python_files = []

    for file_path in (
        project_folder.rglob("*.py")
    ):

        if should_ignore_file(
            file_path,
            project_folder
        ):
            continue

        python_files.append(
            file_path
        )

    return python_files


# =================================================
# REPORT MEMORY CLEANUP
# =================================================

def cleanup_expired_reports():

    current_time = time.time()

    expired_ids = []

    for report_id, report in (
        analysis_reports.items()
    ):

        age = (
            current_time
            - report["created_at"]
        )

        if (
            age
            > REPORT_EXPIRY_SECONDS
        ):
            expired_ids.append(
                report_id
            )

    for report_id in expired_ids:

        analysis_reports.pop(
            report_id,
            None
        )


# =================================================
# FRIENDLY ERROR RESPONSE
# =================================================

def error_response(
    message,
    status_code
):

    return render_template(
        "error.html",
        message=message
    ), status_code


# =================================================
# 413 — UPLOAD TOO LARGE
# =================================================

@app.errorhandler(413)
def upload_too_large(
    error
):

    return error_response(
        "File is too large. Maximum upload size is 10 MB.",
        413
    )


# =================================================
# START APPLICATION
# =================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )