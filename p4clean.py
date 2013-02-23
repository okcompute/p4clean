import os
import argparse
import errno
from commands import getoutput


def delete_empty_folders(root):
    """Delete all empty folders under root (excluding root)"""
    for path, directories, files in os.walk(root, topdown=False):
        if not files and path is not root:
            try:
                print "deleting " + path
                os.rmdir(path)
            except OSError, e:
                if e.errno == errno.ENOTEMPTY:
                    pass


def get_perforce_status_on_folder(path):
    old_path = os.getcwd()
    try:
        os.chdir(path)
        return getoutput("p4 status")
    except Exception:
        return None
    finally:
        os.chdir(old_path)


def get_files_to_delete_from_perforce_status(status):
    pass


def filter_out_exluded_files_from_files_list(files_list):
    pass


def delete_files(files_list):
    pass


def main():
    """The main"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", help="root path from which all child empty folders will be deleted")
    args = parser.parse_args()

    # get the diff between server and local
    perforce_status = get_perforce_status_on_folder(args.path)

    files_to_delete = get_files_to_delete_from_perforce_status(perforce_status)

    delete_files(files_to_delete)

    # Remove any empty folders left by the clean up
    delete_empty_folders(args.path)


if __name__ == "__main__":
    main()
