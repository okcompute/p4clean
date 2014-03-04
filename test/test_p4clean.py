import pytest
import shutil
import stat
import os
import p4clean
from minimock import (
    mock,
    Mock,
    restore,
)
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


def test_delete_empty_folders_error_count():
    """ Test the method `delete_empty_folders` returns the correct errors count
    when os.rmdir() raise exceptions. """

    root_folder = os.tmpnam()

    # Create 3 empty folders
    os.mkdir(root_folder)
    os.mkdir(root_folder + '/folderA')
    os.mkdir(root_folder + '/folderB')
    os.mkdir(root_folder + '/folderC')

    def create_file(root, path):
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()

    # populate random folders with one file
    create_file(root_folder, 'folderA/temp.txt')

    old_cwd = os.getcwd()
    os.chdir(root_folder)

    class FakeConfig(object):
        def is_excluded(self, path):
            return False

    def mock_rmdir(path):
        raise Exception

    mock('os.rmdir', returns_func=mock_rmdir)

    instance = p4clean.P4Clean()
    instance.config = FakeConfig()

    # the tested function call
    deleted_count, error_msgs = instance.delete_empty_folders()

    os.chdir(old_cwd)
    restore()

    assert deleted_count == 0, "No folder should have been deleted"
    assert len(error_msgs) == 2, "All folders should have thrown an error"

    shutil.rmtree(root_folder)


def test_get_perforce_status():
    pass  # We don't test method because we assume that Perfoce is correct.
    # status = p4clean.get_perforce_status('/Users/okcompute/Developer/Perforce/p4clean')
    # print status


def test_delete_untracked_files():
    """ Test P4Clean.delete_untracked_files method."""

    root_folder = os.tmpnam()

    # Create a folder tree
    os.mkdir(root_folder)
    os.mkdir(root_folder + '/folder')

    old_cwd = os.getcwd()
    os.chdir(root_folder)

    def create_file(root, path):
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()

    # populate random folders with one file
    create_file(root_folder, 'folder/tempA.txt')
    create_file(root_folder, 'folder/tempB.txt')
    create_file(root_folder, 'folder/tempC.txt')

    class FakeConfig(object):
        def is_excluded(self, path):
            return False

    class FakePerforce(object):
        def get_untracked_files(self, path):
            return [root_folder + "/folder/tempA.txt",
                    root_folder + "/folder/tempB.txt"]

    Perforce = Mock('P4Clean.Perforce')
    Perforce.mock_returns = Mock('perforce')

    instance = p4clean.P4Clean()
    instance.config = FakeConfig()
    instance.perforce = FakePerforce()

    # the tested function call
    count, msgs = instance.delete_untracked_files()

    os.chdir(old_cwd)
    restore()

    assert count == 2, "Invalid deleted file count"
    assert not os.path.exists(root_folder + '/folder/tempA.txt'), "File should have been deleted"
    assert not os.path.exists(root_folder + '/folder/tempB.txt'), "File should have been deleted"
    assert os.path.exists(root_folder + '/folder/tempC.txt'), "File should not have been deleted"

    shutil.rmtree(root_folder)


def test_delete_untracked_files_on_symlinks():
    """ Test P4Clean.delete_untracked_files method will not delete files
    targeted by a symlinks. Only the symlink itself will be removed. """
    root_folder = os.tmpnam()

    # Create a folder tree
    os.mkdir(root_folder)
    os.mkdir(root_folder + '/folder')

    old_cwd = os.getcwd()
    os.chdir(root_folder)

    def create_file(root, path):
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()

    # populate random folders with one file
    create_file(root_folder, '/tempA.txt')

    os.symlink(root_folder + '/tempA.txt', root_folder + '/folder/tempA.txt')

    class FakeConfig(object):
        def is_excluded(self, path):
            return False

    class FakePerforce(object):
        def get_untracked_files(self, path):
            return [root_folder + "/folder/tempA.txt"]

    Perforce = Mock('P4Clean.Perforce')
    Perforce.mock_returns = Mock('perforce')

    instance = p4clean.P4Clean()
    instance.config = FakeConfig()
    instance.perforce = FakePerforce()

    # the tested function call
    count, msgs = instance.delete_untracked_files()

    os.chdir(old_cwd)
    restore()

    assert count == 1, "Invalid deleted file count"
    assert not os.path.exists(root_folder + '/folder/tempA.txt'), "Symlink should have been deleted"
    assert os.path.exists(root_folder + '/tempA.txt'), "File pointed by symlink should still exist."

    shutil.rmtree(root_folder)


def test_symlinks_source_file_mode_does_not_change():
    """ Test P4Clean.delete_untracked_files method will not change the file
    mode for source of a symlinked file."""
    root_folder = os.tmpnam()

    # Create a folder tree
    os.mkdir(root_folder)
    os.mkdir(root_folder + '/folder')

    old_cwd = os.getcwd()
    os.chdir(root_folder)

    def create_file(root, path):
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()

    # populate random folders with one file
    create_file(root_folder, '/tempA.txt')
    create_file(root_folder, '/folder/tempB.txt')

    # Change the file permissions to read-only
    os.chmod(root_folder + '/tempA.txt', stat.S_IREAD)
    # Backup file A mode
    st_mode = os.stat(root_folder + '/tempA.txt').st_mode

    # Make file Read only too
    os.chmod(root_folder + '/folder/tempB.txt', stat.S_IREAD)

    # Create a symlink on read-only file
    os.symlink(root_folder + '/tempA.txt', root_folder + '/folder/tempA.txt')

    class FakeConfig(object):
        def is_excluded(self, path):
            return False

    class FakePerforce(object):
        def get_untracked_files(self, path):
            return [root_folder + "/folder/tempA.txt",
                    root_folder + "/folder/tempB.txt"]

    Perforce = Mock('P4Clean.Perforce')
    Perforce.mock_returns = Mock('perforce')

    instance = p4clean.P4Clean()
    instance.config = FakeConfig()
    instance.perforce = FakePerforce()

    # the tested function call
    count, msgs = instance.delete_untracked_files()

    os.chdir(old_cwd)
    restore()

    assert count == 2, "Invalid deleted file count"
    assert not os.path.exists(root_folder + '/folder/tempA.txt'), "Symlink should have been deleted."
    assert not os.path.exists(root_folder + '/folder/tempB.txt'), "Read-only file should have been deleted."
    assert os.path.exists(root_folder + '/tempA.txt'), "File pointed by symlink should still exist."
    assert os.stat(root_folder + '/tempA.txt').st_mode == st_mode, "File pointed by symlink should still have same mode."

    shutil.rmtree(root_folder)


pytest.main()
