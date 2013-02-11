import os
import argparse


def is_empty_folder(folder):
    """Return True if the folder is empty"""
    pass


def build_empty_folder_list(path):
    """ Create a lists of all empty folder inside the path"""
    pass


def delete_empty_folders(empty_folders_list):
    pass

def delete_empty_folder(folder):
    """Delete the folder only if it is found to be empty, otherwise
    do nothing"""
    pass


def main():
    """The main"""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="root path from which all child empty folders will be deleted")
    args = parser.parse_args()

    for path, directory, file in os.walk(args.path, topDown=True):
        try:
            os.rmdir(os.path.join(path))
        except OSError, e
        if e.errno == errno.ENOTEMPTY:
            pass
        else:
            print "%s folder delete." % path

if __name__ == "__main__":
    main()
