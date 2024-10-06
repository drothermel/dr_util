import dr_util.file_utils as fu
import numpy as np
import pytest

# Sample data for different formats
sample_data = {
    "json": {"key": "value"},
    "jsonl": [{"key1": "value1"}, {"key2": "value2"}],
    "pkl": {"key": "value"},
    "txt": "Hello, World!",
    "npy": np.array([1, 2, 3]),
    "yaml": {"key": "value"},
}


def test_help():
    helps = fu.fu_help()
    assert helps != ""

    pathlib_helps = fu.pathlib_help()
    assert pathlib_helps != ""


@pytest.mark.parametrize("file_format", ["json", "jsonl", "pkl", "txt", "npy", "yaml"])
def test_dump_load_file(file_format, tmp_path):
    # Generate the appropriate path for the test
    test_file = tmp_path / f"test_file.{file_format}"

    # Dump the file
    assert fu.dump_file(sample_data[file_format], test_file)

    # Load the file
    loaded_data = fu.load_file(test_file)

    # Check if the loaded data matches the original data
    if file_format == "npy":
        assert np.array_equal(loaded_data, sample_data[file_format])
    else:
        assert loaded_data == sample_data[file_format]


@pytest.mark.parametrize("file_format", ["json", "jsonl", "pkl", "txt", "npy", "yaml"])
def test_nonexistent_file_load(file_format, tmp_path):
    # Generate a path that does not exist
    test_file = tmp_path / f"nonexistent_file.{file_format}"

    # Attempt to load the nonexistent file, expecting None as return value
    assert fu.load_file(test_file) is None


@pytest.mark.parametrize("file_format", ["json", "jsonl", "pkl", "txt", "npy", "yaml"])
def test_load_files(file_format, tmp_path):
    # Create multiple test files
    test_file1 = tmp_path / f"test_file1.{file_format}"
    test_file2 = tmp_path / f"test_file2.{file_format}"

    # Dump sample data to both files
    fu.dump_file(sample_data[file_format], test_file1)
    fu.dump_file(sample_data[file_format], test_file2)

    # Load the files using load_files
    files_to_load = [test_file1, test_file2]
    loaded_data = fu.load_files(files_to_load)

    # Verify that the loaded data matches the original data for both files
    if file_format == "npy":
        assert len(loaded_data) == len(files_to_load)
        assert np.array_equal(loaded_data[0], sample_data[file_format])
        assert np.array_equal(loaded_data[1], sample_data[file_format])
    else:
        assert len(loaded_data) == len(files_to_load)
        assert loaded_data[0] == sample_data[file_format]
        assert loaded_data[1] == sample_data[file_format]


@pytest.mark.parametrize("file_format", ["json", "jsonl", "pkl", "txt", "npy", "yaml"])
def test_load_files_with_nonexistent_file(file_format, tmp_path):
    # Create a valid test file and a nonexistent file
    test_file1 = tmp_path / f"test_file1.{file_format}"
    nonexistent_file = tmp_path / f"nonexistent_file.{file_format}"

    # Dump sample data to the valid file
    fu.dump_file(sample_data[file_format], test_file1)

    # Load the files including the nonexistent one
    files_to_load = [test_file1, nonexistent_file]
    loaded_data = fu.load_files(files_to_load)

    # Verify the data: valid data should be loaded, None for the nonexistent file
    if file_format == "npy":
        assert len(loaded_data) == len(files_to_load)
        assert np.array_equal(loaded_data[0], sample_data[file_format])
        assert loaded_data[1] is None
    else:
        assert len(loaded_data) == len(files_to_load)
        assert loaded_data[0] == sample_data[file_format]
        assert loaded_data[1] is None
