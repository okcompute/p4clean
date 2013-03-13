import pytest
import shutil
import os
import itertools
import p4clean
from minimock import mock
from minimock import restore
import ConfigParser
import __builtin__


def unused():
    """ unused function to make linter complain about unused import"""
    ConfigParser()
    __builtin__.open()


def test_delete_empty_folders():
    root_folder = os.tmpnam()

    # Create a folder tree
    os.mkdir(root_folder)
    os.mkdir(root_folder + '/folderA')
    os.mkdir(root_folder + '/folderA/folderAA')
    os.mkdir(root_folder + '/folderB')
    os.mkdir(root_folder + '/folderC')
    os.mkdir(root_folder + '/folderC/folderCC')
    os.mkdir(root_folder + '/folderD')
    os.mkdir(root_folder + '/folderD/folderDD')

    def create_file(root, path):
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()

    # populate random folders with one file
    create_file(root_folder, 'folderA/temp.txt')
    create_file(root_folder, 'folderA/folderAA/temp.txt')
    create_file(root_folder, 'folderD/folderDD/temp.txt')

    # the tested function call
    p4clean.delete_empty_folders(root_folder)

    folder_list = [path for path, directories, files in os.walk(root_folder)]

    assert root_folder in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + '/folderA' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + '/folderA/folderAA' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + '/folderD' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + '/folderD/folderDD' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + '/folderB' not in folder_list, "Folder is empty and should not exist"
    assert root_folder + '/folderC' not in folder_list, "Folder is empty and should not exist"
    assert root_folder + '/folderC/folderCC' not in folder_list, "Folder is empty and should not exist"

    shutil.rmtree(root_folder)


def test_delete_empty_folder_keep_current_folder():
    old_cwd = os.getcwd()
    root_folder = os.tmpnam()

    # Create a folder tree
    os.mkdir(root_folder)
    os.mkdir(root_folder + '/folderA')
    os.mkdir(root_folder + '/folderA/folderAA')

    # set the current working directory to root and test the delete
    # function on the . folder
    os.chdir(root_folder)

    # the tested function call
    p4clean.delete_empty_folders(".")

    folder_list = [path for path, directories, files in os.walk(root_folder)]

    assert len(folder_list) == 1, "Root folder should still exist"
    assert root_folder in folder_list, "Folder is not empty and should still exist"

    os.chdir(old_cwd)
    shutil.rmtree(root_folder)


def test_get_perforce_status():
    pass  # We don't test method because we assume that Perfoce is correct.
    # status = p4clean.get_perforce_status('/Users/okcompute/Developer/Perforce/p4clean')
    # print status


def test_get_files_to_delete_with_excluded_pattern():
    fake_status = "new_folder/haha.txt - reconcile to add \
            //depot/p4clean/new_folder/haha.txt#1\n \
            test.txt - reconcile to add //depot/p4clean/test.txt#1\n \
            test.py - reconcile to add //depot/p4clean/test.py#1\n \
            test.c - reconcile to add //depot/p4clean/test.c#1\n \
            test.h - reconcile to add //depot/p4clean/test.h#1\n \
            test.log - reconcile to add //depot/p4clean/test.log#1"

    config = p4clean.P4CleanConfig(exclusion="*.py;*.c;*.h")

    files_to_delete = p4clean.compute_files_to_delete(config, fake_status)

    print files_to_delete
    assert len(files_to_delete) == 3, "Unexpected numbers of files to delete"
    assert "new_folder/haha.txt" in files_to_delete, "Expected file not found"
    assert "test.txt" in files_to_delete, "Expected file not found"
    assert "test.log" in files_to_delete, "Expected file not found"


def test_delete_files():
    root_folder = os.tmpnam()

    # Create a folder tree
    os.mkdir(root_folder)
    os.mkdir(root_folder + '/folderA')
    os.mkdir(root_folder + '/folderA/folderAA')
    os.mkdir(root_folder + '/folderB')

    def create_file(root, path):
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()
        return temp_file_path

    files = ['folderA/temp.txt', 'folderA/folderAA/temp.txt', 'folderB/temp.txt']

    # populate random folders with one file
    created_files = []
    for file in files:
        created_files.append(create_file(root_folder, file))

    # the tested function call
    p4clean.delete_files(created_files)

    files_list = [files for path, directories, files in os.walk(root_folder)]
    # flatten the list of list to 1 dimension list
    files_list = list(itertools.chain.from_iterable(files_list))

    assert len(files_list) == 0, "All files should have been deleted"

    shutil.rmtree(root_folder)


def test_parse_config_file():
    def config_read(path):
        pass

    def config_get(section, option):
        return '*.txt;test.cpp;*.log;/folder/folder/file.x'

    def open(path, args):
        class unused:
            def __enter__(self):
                return None

            def __exit__(self, type, value, traceback):
                pass
        return unused()

    # def P4CleanConfig_init(self, path, exclusion):
    #     pass

    mock('ConfigParser.RawConfigParser.read', returns_func=config_read)
    mock('ConfigParser.RawConfigParser.get', returns_func=config_get)
    mock('__builtin__.open', returns_func=open)
    # mock('P4CleanConfig.__init__', returns_func=P4CleanConfig_init)

    config = p4clean.P4CleanConfig()

    exclusion_list = config.parse_config_file('path')

    # restore __builtin__.open() because the test system uses it!
    restore()

    assert '*.txt' in exclusion_list, "exclusion pattern should be in list"
    assert 'test.cpp' in exclusion_list, "exclusion pattern should be in list"
    assert '*.log' in exclusion_list, "exclusion pattern should be in list"
    assert '/folder/folder/file.x' in exclusion_list, "exclusion pattern should be in list"


def test_parse_config_file_constructor():
    """ Test the construction of a P4CleanConfig object. Note: this uses a sample
    .p4clean file located in /test/data folder"""
    config = p4clean.P4CleanConfig('./test/data')

    assert config.is_excluded('test.txt'), "File should be exluded"
    assert config.is_excluded('abracadabra.log'), "File should be exluded"
    assert config.is_excluded('/folder/folder/test.txt'), "File should be exluded"
    assert config.is_excluded('/folder/folder/abracadabra.log'), "File should be exluded"
    assert config.is_excluded('test.cpp'), "File should be exluded"
    assert not config.is_excluded('/folder/test.cpp'), "File should be exluded"
    assert not config.is_excluded('file.x'), "File should not be exluded"
    assert config.is_excluded('/folder/folder/file.x'), "File should be exluded"
    assert config.is_excluded('.git/'), "Directory should be exluded"
    assert config.is_excluded('/folder/x/.git/file.x'), "File should be exluded"
    assert config.is_excluded('.ctags'), "File should be exluded"
    assert config.is_excluded('/tata/tata/.ctags'), "File should be exluded"
    assert config.is_excluded('.vimrc'), "File should be exluded"
    assert config.is_excluded('/tata/tata/.vimrc'), "File should be exluded"


pytest.main()
