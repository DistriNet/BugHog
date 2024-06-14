import json
import logging
import os

logger = logging.getLogger(__name__)


def load_experiment_pages(config_folder_path: str, allowed_domains: list[str]) -> dict:
    """
    Expected folder structure:
    - Project
    - Case
        - Domain
        - Subdir
    """
    experiment_pages = {}

    folder_structure = get_folder_structure(config_folder_path)

    projects = [project for project in folder_structure if project["is_folder"]]
    for project in sorted(projects, key=lambda x: x['name']):
        cases = [case for case in project["subfolders"] if case["is_folder"]]
        for case in cases:
            domains = [domain for domain in case["subfolders"] if domain["is_folder"]]
            for domain in domains:
                if domain['name'] not in allowed_domains:
                    raise AttributeError(f"Domain '{domain['name']}' is not allowed ({project['name'], case['name']})")

                if domain["name"] not in experiment_pages:
                    experiment_pages[domain["name"]] = {}

                subdirs = [subdir for subdir in domain["subfolders"] if subdir["is_folder"]]
                for subdir in subdirs:
                    url_path = os.path.join(project['name'], case['name'], subdir['name'])

                    experiment_pages[domain["name"]][url_path] = {}
                    experiment_pages[domain["name"]][url_path]["headers"] = get_headers(subdir["path"])

                    content, content_type_header = get_content(subdir["path"])
                    experiment_pages[domain["name"]][url_path]["content"] = content

                    if not headers_contain_header(experiment_pages[domain["name"]][url_path]["headers"], "Content-Type"):
                        experiment_pages[domain["name"]][url_path]["headers"].append(content_type_header)

        logger.info(f"Project '{project['name']}': Loaded {len(cases)} experiments")
    return experiment_pages


def read_content_file(file_path) -> str:
    with open(file_path, 'r', encoding="utf-8") as file:
        return "".join(file.readlines())


def get_content(subdir_folder_path: str):
    potential_files = [
        {
            "file_name": "index.html",
            "content_type": "text/html"
        },
        {
            "file_name": "index.xml",
            "content_type": "text/xml"
        },
        {
            "file_name": "index.css",
            "content_type": "text/css"
        },
        {
            "file_name": "index.js",
            "content_type": "text/javascript"
        }
    ]
    content = None
    for file in potential_files:
        file_path = os.path.join(subdir_folder_path, file["file_name"])
        content_type = file["content_type"]
        if os.path.isfile(file_path):
            content = read_content_file(file_path)
            content_type_header = {"key": "Content-Type", "value": content_type}
            break
    if content is None:
        raise AttributeError(f"No valid file found in '{subdir_folder_path}'")
    return content, content_type_header


def get_headers(subdir_folder_path: str) -> list:
    file_path = os.path.join(subdir_folder_path, "headers.json")
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            try:
                json_content = json.load(file)
            except json.decoder.JSONDecodeError as e:
                raise AttributeError(f"Could not parse headers.json in '{subdir_folder_path}'") from e
            if not isinstance(json_content, list):
                raise AttributeError(f"headers.json in '{subdir_folder_path}' is not a list")
            return json_content
    else:
        return []


def headers_contain_header(headers: list, target_header: str) -> bool:
    for header in headers:
        if header_name := header.get('key', None):
            if header_name.lower() == target_header.lower():
                return True
        else:
            logger.warning(f"Header does not contain 'key' attribute: {header}. Skipping.")
    return False


def get_folder_structure(root_folder_path: str) -> list:
    folder_structure = []
    if not os.path.isdir(root_folder_path):
        raise AttributeError(f"Given root folder path does not point to a folder ({root_folder_path})")
    for subdir in os.listdir(root_folder_path):
        subdir_path = os.path.join(root_folder_path, subdir)
        is_folder = os.path.isdir(subdir_path)
        folder_structure.append({
            "name": subdir,
            "path": subdir_path,
            "is_folder": is_folder,
            "subfolders": get_folder_structure(subdir_path) if is_folder else None
        })
    return folder_structure


def get_all_subdirs(root_path: str) -> list:
    subdirs = list()
    for project_folder in os.listdir(root_path):
        project_folder_path = os.path.join(root_path, project_folder)
        if not os.path.isdir(project_folder_path):
            continue
        for case_folder in os.listdir(project_folder_path):
            case_folder_path = os.path.join(project_folder_path, case_folder)
            if os.path.isdir(case_folder_path):
                subdirs.append(case_folder_path)
    return subdirs
