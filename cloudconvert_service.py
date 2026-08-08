import os
import tempfile
from urllib.error import URLError
from urllib.request import urlopen

import cloudconvert


class CloudConvertError(Exception):
    pass


SUPPORTED_INPUT_FORMATS = {"doc", "docx", "odt"}


def resolve_sandbox_mode() -> bool:
    value = (os.environ.get("CLOUDCONVERT_SANDBOX") or "").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off", ""}:
        return False
    return False


def _raise_cloudconvert_response_error(response: dict, action: str) -> None:
    if not isinstance(response, dict):
        raise CloudConvertError(f"CloudConvert failed to {action}. Unexpected response type: {type(response).__name__}.")

    if response.get("id"):
        return

    error = response.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or str(error)
        raise CloudConvertError(f"CloudConvert failed to {action}. {message}")

    message = response.get("message")
    if message:
        raise CloudConvertError(f"CloudConvert failed to {action}. {message}")

    raise CloudConvertError(f"CloudConvert failed to {action}. Invalid response from SDK.")


def _extract_task_by_operation(job: dict, operation: str) -> dict:
    tasks = job.get("tasks", [])
    if isinstance(tasks, dict):
        tasks = tasks.values()

    for task in tasks:
        if isinstance(task, dict) and task.get("operation") == operation:
            return task

    raise CloudConvertError(f"CloudConvert task with operation '{operation}' was not found in the job response.")


def get_input_format(filename: str) -> str:
    _, extension = os.path.splitext(filename or "")
    file_format = extension.lower().lstrip(".")
    if file_format not in SUPPORTED_INPUT_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_INPUT_FORMATS))
        raise CloudConvertError(f"Unsupported file type '{extension or '(none)'}'. Supported types: {supported}.")
    return file_format


def get_engine_config(input_format: str) -> tuple[str, str]:
    if input_format == "odt":
        return "libreoffice", "26.2.4"
    return "office", "2.1"


def create_conversion_job(input_format: str) -> dict:
    engine, engine_version = get_engine_config(input_format)
    job = cloudconvert.Job.create(payload={
        "tasks": {
            "poem_upload": {
                "operation": "import/upload"
            },
            "poem_pdf": {
                "operation": "convert",
                "input_format": input_format,
                "output_format": "pdf",
                "engine": engine,
                "input": "poem_upload",
                "engine_version": engine_version
            },
            "poem_export": {
                "operation": "export/url",
                "input": "poem_pdf",
                "inline": False,
                "archive_multiple_files": False
            }
        }
    })
    _raise_cloudconvert_response_error(job, "create the job")
    return job


def download_converted_file(export_task: dict) -> tuple[bytes, str]:
    files = export_task.get("result", {}).get("files", [])
    if not files:
        raise CloudConvertError("CloudConvert did not return a converted file.")

    file_info = files[0]
    try:
        with urlopen(file_info["url"]) as response:
            return response.read(), file_info.get("filename", "converted.pdf")
    except URLError as exc:
        raise CloudConvertError(f"Failed to download converted file. {exc}") from exc


def convert_office_to_pdf(uploaded_file, api_key: str, filename: str | None = None, sandbox: bool | None = None) -> tuple[bytes, str]:
    if not api_key:
        raise CloudConvertError("A CloudConvert API key is required.")

    sandbox_mode = resolve_sandbox_mode() if sandbox is None else sandbox

    source_name = filename or uploaded_file.filename or "document.docx"
    input_format = get_input_format(source_name)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(source_name)[1])
    temp_path = temp_file.name
    temp_file.close()
    uploaded_file.save(temp_path)

    try:
        cloudconvert.configure(api_key=api_key, sandbox=sandbox_mode)
        job = create_conversion_job(input_format)
        job_id = job["id"]
        upload_task_id = _extract_task_by_operation(job, "import/upload").get("id")
        upload_task = cloudconvert.Task.find(id=upload_task_id)
        cloudconvert.Task.upload(file_name=temp_path, task=upload_task)
        import_task = cloudconvert.Task.wait(id=upload_task_id)
        import_status = (import_task or {}).get("status")
        if import_status == "error":
            import_message = import_task.get("message") or import_task.get("code") or "Upload failed."
            raise CloudConvertError(f"CloudConvert import/upload task failed. {import_message}")
        if import_status != "finished":
            raise CloudConvertError(f"CloudConvert import/upload task ended with status '{import_status}'.")
        job = cloudconvert.Job.wait(id=job_id)
        _raise_cloudconvert_response_error(job, "wait for the job")
        export_task = _extract_task_by_operation(job, "export/url")
        return download_converted_file(export_task)
    except CloudConvertError:
        raise
    except Exception as exc:
        raise CloudConvertError(f"CloudConvert failed. {exc}") from exc
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)