import os


def find_file_upwards(filename, start_path=__file__):
    """
    Traverses up from start_path to find a file with the given filename.

    Parameters:
    - filename (str): The name of the file to find.
    - start_path (str): The initial path from where to start the search, defaults to __file__.

    Returns:
    - str: The full path to the file if found, otherwise None.
    """
    # Get the absolute path of the start location
    current_path = os.path.abspath(start_path)

    # Traverse up the directories
    while os.path.dirname(current_path) != current_path:
        current_path = os.path.dirname(current_path)
        possible_file = os.path.join(current_path, filename)

        # Check if the file exists in this directory
        if os.path.isfile(possible_file):
            return possible_file

    # Return None if the file has not been found
    return None


def find_directory_of_file(filename, start_path=__file__):
    hit = find_file_upwards(filename, start_path=start_path)
    if hit is not None:
        return os.path.dirname(hit)
    return None


# Usage example:
# found_file = find_file_upwards('target_filename.txt')
# print("Found file at:", found_file)
