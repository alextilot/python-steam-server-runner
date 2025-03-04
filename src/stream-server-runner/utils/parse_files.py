import logging
import re

log = logging.getLogger(__name__)


def _parse_acf_string(acf_string: str) -> dict:
    data = {}
    stack = [data]
    key_value_pattern = re.compile(r'"(.*?)"\s+"(.*?)"')
    block_start_pattern = re.compile(r'"(.*?)"')

    for line in acf_string.splitlines():
        line = line.strip()
        if line == "" or line == "{":
            continue
        if line == "}":
            stack.pop()
        elif line.count('"') > 2:
            key, value = key_value_pattern.findall(line)[0]
            stack[-1][key] = value
        elif line.count('"') == 2:
            key = block_start_pattern.findall(line)[0]
            new_dict = {}
            stack[-1][key] = new_dict
            stack.append(new_dict)
    return data


def read_acf_file(file_path: str) -> dict | None:
    if not file_path.endswith(".acf"):
        log.error(f"File does not end in *.acf: {file_path}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_string = file.read()
            return _parse_acf_string(file_string)
    except FileNotFoundError:
        log.error(f"File not found: {file_path}")
        return None
