import os
import argparse
import errno

def delete_empty_folders(root):
    """Delete the folders only if it is found to be empty, otherwise
    do nothing"""
    for path, directories, files in os.walk(root, topdown=False):
        print "path is being checked :files %d    dir %d " % (len(files), len(directories)) + path
        if not files:
            try:
                print "deleting " + path
                os.rmdir(path)
            except OSError, e:
                if e.errno == errno.ENOTEMPTY:
                    pass


def main():
    """The main"""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="root path from which all child empty folders will be deleted")
    args = parser.parse_args()

    # Remove any empty folders left by the clean up
    delete_empty_folders(args.path)


if __name__ == "__main__":
    main()
