import pytest
from p4-clean import delete_empty_folder

def test_delete_empty_folder():
    """Test the function delete_empty_folder."""
    # Preparation
    empty_folder = os.tmpdir()
    os.mkdir(empty_folder)

    # The function to test
    delete_emtpty_folder(emtpy_folder)

    assert os.access("empty_folder", os.R_OK) "Folder should be empty"

    os.rmdir(empty_folder)

pytest.main()
