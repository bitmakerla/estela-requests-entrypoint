import logging
import re
import os
from requests_entrypoint.settings import BLOCKED_NAMES
from requests_entrypoint.exceptions import ProjectStructureException

logger = logging.getLogger(__name__)

def get_file_by_spider_name(directory: str, spider_name: str) -> str:
    """
    Search for a file in the given directory that contains a variable
    named 'spider_name' and return its name.

    Args:
        directory (str): The path to the directory to search in.

    Returns:
        str: The name of the file containing the 'spider_name' variable.
             None if not found.
    """
    try: 
        file_names = [file for file in os.listdir(directory) if file not in BLOCKED_NAMES]

        # Iterate over all files in directory
        for file_name in file_names:
            if file_name.endswith(".py"):
                # Read file contents and search for spider_name variable
                with open(os.path.join(directory, file_name), "r") as file:
                    source_code = file.read()
                    match = re.search(r"spider_name\s*=\s*['\"]([^'\"]+)['\"]", source_code)
                    try:
                        if match.group(1) == spider_name:
                            return file_name
                    except Exception:
                        pass
    except Exception as e:
        raise ProjectStructureException(str(e))

def get_spider_names(directory: str) -> list:
    """
    Given a directory, returns a list of spider names.
    A spider name is defined as the value assigned to the variable spider_name
    in any Python file in the directory that ends with .py.

    :param directory: The directory to search for spider names.
    :return: A list of spider names.
    """
    try: 
        # List comprehension to get all file names in the directory
        file_names = [file for file in os.listdir(directory) if file not in BLOCKED_NAMES]

        # List to store spider names
        spider_names = []

        # Loop through each file name
        for file_name in file_names:
            # Only consider Python files
            if file_name.endswith(".py"):
                # Open the file and read its contents
                with open(os.path.join(directory, file_name), "r") as file:
                    source_code = file.read()

                    # Search for the spider_name variable in the source code
                    match = re.search(r"spider_name\s*=\s*['\"]([^'\"]+)['\"]", source_code)

                    # If a match is found, add the spider name to the list
                    if match:
                        spider_name = match.group(1)
                        spider_names.append(spider_name)

        return spider_names
    except Exception as e :
        raise ProjectStructureException(str(e))
