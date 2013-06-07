import pytest
import shutil
import os
import p4clean
from minimock import mock
from minimock import restore
import ConfigParser
import __builtin__


def unused():
    """ unused function to make linter complain about unused import"""
    ConfigParser()
    __builtin__.open()


def test_perforce_get_untracked_files():

    # def Perforce2012_init():
    #     pass

    def Perforce_get_perforce_fstat(path):
        return "... clientFile /path/test.log \n \
                ... clientFile /path/blarg/file.txt \n \
                ... clientFile /path/path2/code.c "

    def Perforce_info():
        return (2010, 'dummy')

    def os_walk(root):
        # emulate a directory hiearchy
        return [("/path", ['blarg', 'test'], ['test.log', 'newfile.c', 'newfile.h'])]

    mock('p4clean.Perforce.info', returns_func=Perforce_info)
    mock('p4clean.Perforce._get_perforce_fstat',
         returns_func=Perforce_get_perforce_fstat)
    mock('os.walk', returns_func=os_walk)

    untracked_files = p4clean.Perforce().get_untracked_files("dummy")

    restore()

    assert len(untracked_files) == 2, "Unexpected numbers of files to delete"
    assert "/path/newfile.c" in untracked_files, "Expected file not found"
    assert "/path/newfile.h" in untracked_files, "Expected file not found"


def test_perforce_2012_get_untracked_files():

    def Perforce2012_init():
        pass

    def Perforce_info():
        return (2012, "//")

    def Perforce2012_get_perforce_status(path):
        return "new_folder/haha.txt - reconcile to add \
            //depot/p4clean/new_folder/haha.txt#1\n \
            test.txt - reconcile to add //depot/p4clean/test.txt#1\n \
            test.py - reconcile to add //depot/p4clean/test.py#1\n \
            test.c - reconcile to add //depot/p4clean/test.c#1\n \
            test.h - reconcile to add //depot/p4clean/test.h#1\n \
            test.log - reconcile to add //depot/p4clean/test.log#1"

    mock('p4clean.Perforce2012.__init__', returns_func=Perforce2012_init)
    mock('p4clean.Perforce.info', returns_func=Perforce_info)
    mock('p4clean.Perforce2012._get_perforce_status',
         returns_func=Perforce2012_get_perforce_status)

    untracked_files = p4clean.Perforce2012().get_untracked_files("dummy")

    restore()

    assert len(untracked_files) == 6, "Unexpected numbers of files to delete"
    assert "new_folder/haha.txt" in untracked_files, "Expected file not found"
    assert "test.txt" in untracked_files, "Expected file not found"
    assert "test.log" in untracked_files, "Expected file not found"


def test_parse_config_file():
    def P4CleanConfig_init():
        pass

    mock('p4clean.P4CleanConfig.__init__', returns_func=P4CleanConfig_init)
    config = p4clean.P4CleanConfig()
    restore()

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'data',
                        '.p4clean')
    exclusion_list = config.parse_config_file(path)

    assert exclusion_list, "exclusion list should not be empty"
    assert '*.txt' in exclusion_list, "exclusion pattern should be in list"
    assert 'test.cpp' in exclusion_list, "exclusion pattern should be in list"
    assert '*.log' in exclusion_list, "exclusion pattern should be in list"
    assert '/folder/folder/file.x' in exclusion_list, "exclusion pattern should be in list"


def test_parse_config_file_no_file():
    def P4CleanConfig_init():
        pass

    mock('p4clean.P4CleanConfig.__init__', returns_func=P4CleanConfig_init)
    config = p4clean.P4CleanConfig()
    restore()

    path = os.path.abspath('.')
    exclusion_list = config.parse_config_file(path)

    assert not exclusion_list, "Exclusion list should be empty."


def test_p4clean_config_constructor():
    """ Test the construction of a P4CleanConfig object. Note: this uses a sample
    .p4clean file located in /test/data folder"""
    def P4CleanConfig_config_file_path(perforce_root):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'data',
                            '.p4clean')

    mock('p4clean.P4CleanConfig.config_file_path',
         returns_func=P4CleanConfig_config_file_path)

    config = p4clean.P4CleanConfig('./test/data')

    restore()

    assert config.is_excluded('test.txt'), "File should be exluded"
    assert config.is_excluded('abracadabra.log'), "File should be exluded"
    assert config.is_excluded(
        '/folder/folder/test.txt'), "File should be exluded"
    assert config.is_excluded(
        '/folder/folder/abracadabra.log'), "File should be exluded"
    assert config.is_excluded('test.cpp'), "File should be exluded"
    assert not config.is_excluded('/folder/test.cpp'), "File should be exluded"
    assert not config.is_excluded('file.x'), "File should not be exluded"
    assert config.is_excluded(
        '/folder/folder/file.x'), "File should be exluded"
    assert config.is_excluded(
        '/Users/test/project/.git'), "Directory should be exluded"
    assert config.is_excluded(
        '/folder/x/.git/file.x'), "File should be exluded"
    assert config.is_excluded('/.git'), "File should be exluded"
    assert config.is_excluded('.ctags'), "File should be exluded"
    assert config.is_excluded('/tata/tata/.ctags'), "File should be exluded"
    assert config.is_excluded('.vimrc'), "File should be exluded"
    assert config.is_excluded('/tata/tata/.vimrc'), "File should be exluded"


def test_config_file_path():
    def P4CleanConfig_init():
        pass

    old_cwd = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))

    mock('p4clean.P4CleanConfig.__init__', returns_func=P4CleanConfig_init)
    config = p4clean.P4CleanConfig()
    restore()

    path = config.config_file_path('')
    os.chdir(old_cwd)

    assert path == os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'data',
                                '.p4clean'), "Unexpected config file path"


def test_config_file_path_empty():
    def P4CleanConfig_init():
        pass

    mock('p4clean.P4CleanConfig.__init__', returns_func=P4CleanConfig_init)
    config = p4clean.P4CleanConfig()
    restore()

    path = config.config_file_path("")
    assert path is None, "Unexpected config file path"


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

    old_cwd = os.getcwd()
    os.chdir(root_folder)

    def create_file(root, path):
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()

    # populate random folders with one file
    create_file(root_folder, 'folderA/temp.txt')
    create_file(root_folder, 'folderA/folderAA/temp.txt')
    create_file(root_folder, 'folderD/folderDD/temp.txt')

    class FakeConfig(object):
        def is_excluded(self, path):
            return False

    def P4Clean_init():
        pass

    mock('p4clean.P4Clean.__init__', returns_func=P4Clean_init)

    instance = p4clean.P4Clean()
    instance.config = FakeConfig()

    # the tested function call
    instance.delete_empty_folders()

    os.chdir(old_cwd)
    restore()

    folder_list = [path for path, directories, files in os.walk(root_folder)]

    assert root_folder in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + \
        '/folderA' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + \
        '/folderA/folderAA' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + \
        '/folderD' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + \
        '/folderD/folderDD' in folder_list, "Folder is not empty and should still  exist"
    assert root_folder + \
        '/folderB' not in folder_list, "Folder is empty and should not exist"
    assert root_folder + \
        '/folderC' not in folder_list, "Folder is empty and should not exist"
    assert root_folder + \
        '/folderC/folderCC' not in folder_list, "Folder is empty and should not exist"

    shutil.rmtree(root_folder)


def test_get_perforce_status():
    pass  # We don't test method because we assume that Perfoce is correct.
    # status = p4clean.get_perforce_status('/Users/okcompute/Developer/Perforce/p4clean')
    # print status


def test_delete_untracked_files():
    "No test needed. This function is too simple."
    pass

pytest.main()
