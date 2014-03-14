import unittest2
import shutil
import stat
import os
import tempfile
import platform
from mock import (
    patch,
    Mock,
)
from p4clean import (
    P4Clean,
    P4CleanConfig,
    Perforce,
)


class P4CleanTests(unittest2.TestCase):

    """P4Clean module test class."""

    def _create_file(self, root, path):
        """ Create a empty file for testing purpose. """
        temp_file_path = root + '/' + path
        temp_file = open(temp_file_path, "wb")
        temp_file.write("")
        temp_file.close()

    @patch('os.walk')
    def test_perforce_get_untracked_files(self, mock_os_walk):
        """ Test Perforce `get_untracked_files` method. """
        # patch os.walk return value
        mock_os_walk.return_value = [("/path", ['blarg', 'test'], ['test.log',
                                                                   'newfile.c',
                                                                   'newfile.h'])]

        with patch.object(Perforce, 'info') as info_mock:
            # Mock Perforce.info() method
            info_mock.return_value = (2010, 'dummy')
            perforce = Perforce()
            # Mock _get_perforce_fstat
            perforce._get_perforce_fstat = Mock()
            perforce._get_perforce_fstat.return_value = \
                "...clientFile /path/test.log \n \
                ... clientFile /path/blarg/file.txt \n \
                ... clientFile /path/path2/code.c "
            perforce.is_inside_symbolic_folder = Mock()
            perforce.is_inside_symbolic_folder.return_value = False

            # The test
            untracked_files = perforce.get_untracked_files("dummy")

        self.assertEqual(len(untracked_files), 2)
        self.assertTrue(os.path.normpath("/path/newfile.c") in untracked_files)
        self.assertTrue(os.path.normpath("/path/newfile.h") in untracked_files)

    @patch('os.walk')
    def test_get_untracked_files_with_same_filename_different_case(self,
                                                                   mock_os_walk):
        """ Test P4Clean differentiates untracked files with same filename but
        different case."""
        # This test cannot be ran under windows. System is case insensitive.
        if platform.system() == 'Windows':
            return

        # patch os.walk return value
        mock_os_walk.return_value = [("/path", [], ['test.log',
                                                    'TEST.log',
                                                    'readme.txt',
                                                    'README.txt',
                                                    'ReAdMe.TxT'])]

        with patch.object(Perforce, 'info') as info_mock:
            # Mock Perforce.info() method
            info_mock.return_value = (2010, 'dummy')

            perforce = Perforce()
            # Mock _get_perforce_fstat
            perforce._get_perforce_fstat = Mock()
            perforce._get_perforce_fstat.return_value = \
                "... clientFile /path/readme.txt \n \
                ... clientFile /path/README.txt \n \
                ... clientFile /path/path2/code.c "
            perforce.is_inside_symbolic_folder = Mock()
            perforce.is_inside_symbolic_folder.return_value = False

            # The test
            untracked_files = perforce.get_untracked_files("dummy")

        self.assertEqual(len(untracked_files), 3)
        self.assertTrue("/path/test.log" in untracked_files)
        self.assertTrue("/path/TEST.log" in untracked_files)
        self.assertTrue("/path/ReAdMe.TxT" in untracked_files)

    @patch('os.getcwd')
    def test_parse_config_file(self, mock_os_getcwd):
        """ Test P4CleanConfig parsing with a real file. """
        # Force working directory to data test folder
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'data')
        # Mock os.getcwd()
        mock_os_getcwd.return_value = path

        config = P4CleanConfig(path + '/.p4clean')

        self.assertTrue(config.is_excluded("tags"))
        self.assertTrue(config.is_excluded(".vimrc"))
        self.assertTrue(config.is_excluded("test.cpp"))
        self.assertTrue(config.is_excluded("test.txt"))
        self.assertTrue(config.is_excluded(".test.txt"))
        self.assertTrue(config.is_excluded("/test.txt"))
        self.assertTrue(config.is_excluded("/.test.txt"))
        self.assertTrue(config.is_excluded("/folder/folder/test.txt"))
        self.assertTrue(config.is_excluded("/folder/folder/file.x"))
        self.assertTrue(config.is_excluded("/.git"))
        self.assertTrue(config.is_excluded("folder/.git"))
        self.assertTrue(config.is_excluded("folder/.git/test"))
        self.assertTrue(config.is_excluded("/folder/folder/.git"))
        self.assertTrue(config.is_excluded("folder/.git/folder/test.log"))
        self.assertTrue(config.is_excluded("/folder/folder/.git/folder/test.log"))
        self.assertFalse(config.is_excluded(".blarg"))
        self.assertFalse(config.is_excluded("/.blarg"))
        self.assertFalse(config.is_excluded("/.blarg/blarg"))
        self.assertFalse(config.is_excluded("/blarg"))
        self.assertFalse(config.is_excluded("/blarg/blarg/blarg"))

    def test_parse_config_file_no_file(self):
        """ Test P4CleanConfig parsing when file not found. """
        path = os.path.abspath('.')
        config = P4CleanConfig(path)

        self.assertFalse(config.is_excluded("tags"))
        self.assertFalse(config.is_excluded(".vimrc"))
        self.assertFalse(config.is_excluded("test.cpp"))
        self.assertFalse(config.is_excluded("test.txt"))
        self.assertFalse(config.is_excluded(".test.txt"))
        self.assertFalse(config.is_excluded("/test.txt"))
        self.assertFalse(config.is_excluded("/.test.txt"))
        self.assertFalse(config.is_excluded("/folder/folder/test.txt"))
        self.assertFalse(config.is_excluded("/folder/folder/file.x"))
        self.assertFalse(config.is_excluded("/.git"))
        self.assertFalse(config.is_excluded("folder/.git"))
        self.assertFalse(config.is_excluded("folder/.git/test"))
        self.assertFalse(config.is_excluded("/folder/folder/.git"))
        self.assertFalse(config.is_excluded("folder/.git/folder/test.log"))
        self.assertFalse(config.is_excluded("/folder/folder/.git/folder/test.log"))
        self.assertFalse(config.is_excluded(".blarg"))
        self.assertFalse(config.is_excluded("/.blarg"))
        self.assertFalse(config.is_excluded("/.blarg/blarg"))
        self.assertFalse(config.is_excluded("/blarg"))
        self.assertFalse(config.is_excluded("/blarg/blarg/blarg"))

    def test_config_file_path_empty(self):
        """ Test P4CleanConfig._config_file_path method returns `None` if no
        root is provided."""
        config = P4CleanConfig('.')

        path = config._config_file_path("")

        self.assertIsNone(path)

    @patch('p4clean.Perforce')
    def test_delete_empty_folders(self, mock_perforce):
        """ Test P4Clean 'delete empty folders' feature. """
        instance = mock_perforce.return_value
        instance.get_untracked_files.return_value = []
        instance.root = '.'

        root_folder = tempfile.mkdtemp()

        # Create a folder tree
        os.mkdir(root_folder + '/folderA')
        os.mkdir(root_folder + '/folderA/folderAA')
        os.mkdir(root_folder + '/folderB')
        os.mkdir(root_folder + '/folderC')
        os.mkdir(root_folder + '/folderC/folderCC')
        os.mkdir(root_folder + '/folderD')
        os.mkdir(root_folder + '/folderD/folderDD')

        old_cwd = os.getcwd()
        os.chdir(root_folder)

        # populate random folders with one file
        self._create_file(root_folder, 'folderA/temp.txt')
        self._create_file(root_folder, 'folderA/folderAA/temp.txt')
        self._create_file(root_folder, 'folderD/folderDD/temp.txt')

        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            # patched method `parse_args` to return `quiet` and `dry_run` as
            # False and `exclude` as `None`
            mock_parse_args.return_value = Mock(quiet=False, dry_run=False,
                                                exclude=None)
            P4Clean().run()

        os.chdir(old_cwd)

        folder_list = [path for path, directories, files in os.walk(root_folder)]

        self.assertTrue(root_folder in folder_list)
        self.assertTrue(os.path.normpath(root_folder + '/folderA') in folder_list)
        self.assertTrue(os.path.normpath(root_folder + '/folderA/folderAA') in folder_list)
        self.assertTrue(os.path.normpath(root_folder + '/folderD') in folder_list)
        self.assertTrue(os.path.normpath(root_folder + '/folderD/folderDD') in folder_list)
        self.assertFalse(os.path.normpath(root_folder + '/folderB') in folder_list)
        self.assertFalse(os.path.normpath(root_folder + '/folderC') in folder_list)
        self.assertFalse(os.path.normpath(root_folder + '/folderC/folderCC') in folder_list)

        shutil.rmtree(root_folder)

    @patch('p4clean.Perforce')
    def test_delete_empty_folders_error_count(self, mock_perforce):
        """ Test P4Clean method `delete_empty_folders` returns the correct
        errors count when os.rmdir() raise exceptions. """
        instance = mock_perforce.return_value
        instance.get_untracked_files.return_value = []

        root_folder = tempfile.mkdtemp()

        # Create 3 empty folders
        os.mkdir(root_folder + '/folderA')
        os.mkdir(root_folder + '/folderB')
        os.mkdir(root_folder + '/folderC')

        # populate random folders with one file
        self._create_file(root_folder, 'folderA/temp.txt')

        old_cwd = os.getcwd()
        os.chdir(root_folder)

        with patch('p4clean.P4CleanConfig') as mock_p4clean_config:
            # Mock config so there is no exclusion
            mock_config = mock_p4clean_config.return_value
            mock_config.is_excluded.return_value = False

            with patch('os.rmdir') as mock_rmdir:
                # mock rmdir to raise exception
                mock_rmdir.side_effect = Exception('Boom')

                instance = P4Clean()
                instance.config = mock_config

                # the tested function call
                empty_deleted_count, error_msgs = instance.delete_empty_folders()

        os.chdir(old_cwd)
        # restore()

        assert empty_deleted_count == 0, "No folder should have been deleted"
        assert len(error_msgs) == 2, "All folders should have thrown an error"

        shutil.rmtree(root_folder)

    @patch('p4clean.Perforce')
    @patch('p4clean.P4CleanConfig')
    def test_delete_untracked_files(self, mock_p4clean_config, mock_perforce):
        """ Test P4Clean `delete_untracked_files` method. """
        root_folder = tempfile.mkdtemp()

        # Mock Perforce class to return a predefined list of untracked files.
        perforce = mock_perforce.return_value
        perforce.get_untracked_files.return_value = [
            root_folder + "/folder/tempA.txt", root_folder + "/folder/tempB.txt"]

        # Mock config to not exclude any file
        config = mock_p4clean_config.return_value
        config.is_excluded.return_value = False

        # Create a folder tree
        os.mkdir(root_folder + '/folder')

        old_cwd = os.getcwd()
        os.chdir(root_folder)

        # populate random folders with one file
        self._create_file(root_folder, 'folder/tempA.txt')
        self._create_file(root_folder, 'folder/tempB.txt')
        self._create_file(root_folder, 'folder/tempC.txt')

        # The tested instance
        instance = P4Clean()

        # Attach mocked config and perforce instance
        instance.config = config
        instance.perforce = perforce

        # the tested function call
        count, msgs = instance.delete_untracked_files()

        os.chdir(old_cwd)

        self.assertEqual(count, 2)
        self.assertFalse(os.path.exists(root_folder + '/folder/tempA.txt'))
        self.assertFalse(os.path.exists(root_folder + '/folder/tempB.txt'))
        self.assertTrue(os.path.exists(root_folder + '/folder/tempC.txt'))

        shutil.rmtree(root_folder)

    @patch('p4clean.Perforce')
    @patch('p4clean.P4CleanConfig')
    def test_delete_untracked_files_on_symlinks(self, mock_p4clean_config, mock_perforce):
        """ Test P4Clean `delete_untracked_files` method will not delete files
        targeted by a symlinks. Only the symlink itself will be removed. """
        # This test cannot be ran under windows. os.symlink does not exist.
        if platform.system() == 'Windows':
            return

        root_folder = tempfile.mkdtemp()

        # Mock Perforce class to return a predefined list of untracked files.
        perforce = mock_perforce.return_value
        perforce.get_untracked_files.return_value = [root_folder + "/folder/tempA.txt"]

        # Mock config to not exclude any file
        config = mock_p4clean_config.return_value
        config.is_excluded.return_value = False

        # Create a folder tree
        os.mkdir(root_folder + '/folder')

        old_cwd = os.getcwd()
        os.chdir(root_folder)

        # Create one file to be symlinked. This file will be set as tracked by
        # perforce and should not be deleted
        self._create_file(root_folder, '/tempA.txt')

        # Symlink the file. The symlink and only the symlink should be deleted
        os.symlink(root_folder + '/tempA.txt', root_folder + '/folder/tempA.txt')

        instance = P4Clean()
        instance.config = config
        instance.perforce = perforce

        # the tested function call
        count, msgs = instance.delete_untracked_files()

        os.chdir(old_cwd)
        # restore()

        self.assertEqual(count, 1)
        self.assertFalse(os.path.exists(root_folder + '/folder/tempA.txt'))
        self.assertTrue(os.path.exists(root_folder + '/tempA.txt'))

        shutil.rmtree(root_folder)

    @patch('p4clean.Perforce')
    @patch('p4clean.P4CleanConfig')
    def test_symlinks_source_file_mode_does_not_change(self, mock_p4clean_config, mock_perforce):
        """ Test P4Clean `delete_untracked_files` method will not change the file
        mode for source of a symlinked file."""
        # This test cannot be ran under windows. os.symlink does not exist.
        if platform.system() == 'Windows':
            return

        root_folder = tempfile.mkdtemp()

        # Mock Perforce class to return a predefined list of untracked files.
        perforce = mock_perforce.return_value
        perforce.get_untracked_files.return_value = [
            root_folder + "/folder/tempA.txt", root_folder + "/folder/tempB.txt"]

        # Mock config to not exclude any file
        config = mock_p4clean_config.return_value
        config.is_excluded.return_value = False

        # Create a folder tree
        os.mkdir(root_folder + '/folder')

        old_cwd = os.getcwd()
        os.chdir(root_folder)

        # populate folders
        self._create_file(root_folder, '/tempA.txt')
        self._create_file(root_folder, '/folder/tempB.txt')

        # Change the file permissions to read-only
        os.chmod(root_folder + '/tempA.txt', stat.S_IREAD)
        # Backup file A mode for validation
        st_mode = os.stat(root_folder + '/tempA.txt').st_mode

        # Make file Read only too
        os.chmod(root_folder + '/folder/tempB.txt', stat.S_IREAD)

        # Create a symlink on read-only file
        os.symlink(root_folder + '/tempA.txt', root_folder + '/folder/tempA.txt')

        instance = P4Clean()
        instance.config = config
        instance.perforce = perforce

        # the tested function call
        count, msgs = instance.delete_untracked_files()

        os.chdir(old_cwd)

        self.assertEqual(count, 2)
        self.assertFalse(os.path.exists(root_folder + '/folder/tempA.txt'))
        self.assertFalse(os.path.exists(root_folder + '/folder/tempB.txt'))
        self.assertTrue(os.path.exists(root_folder + '/tempA.txt'))
        self.assertEqual(os.stat(root_folder + '/tempA.txt').st_mode, st_mode)

        shutil.rmtree(root_folder)
