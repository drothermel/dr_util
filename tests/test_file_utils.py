import dr_util.file_utils as fu
import numpy as np

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
    helps = fu.help_str()
    assert helps != ""


# Expected file suffixes and corresponding correct loading methods
suffix_map = {
    "json": "json",
    "jsonl": "jsonl",
    "pkl": "pkl",
    "txt": "txt",
    "npy": "npy",
    "yaml": "yaml",
}


@pytest.mark.parametrize(
    "original_format,force_format",
    [
        ("json", "pkl"),
        ("txt", "json"),
        ("yaml", "txt"),
        ("jsonl", "json"),
        ("npy", "pkl"),
        ("pkl", "json"),
    ],
)
def test_dump_load_with_force_suffix(original_format, force_format, tmp_path):
    # Generate the appropriate path for the test
    test_file = tmp_path / f"test_file.{original_format}"

    # Dump the file with the forced suffix
    assert fu.dump_file(
        sample_data[original_format], test_file, force_suffix=force_format
    )

    # Load the file with the forced suffix
    loaded_data = fu.load_file(test_file, force_suffix=force_format)

    # Check if the loaded data matches the original data
    if force_format == "npy":
        assert np.array_equal(loaded_data, sample_data[original_format])
    else:
        assert loaded_data == sample_data[original_format]


@pytest.mark.parametrize(
    "original_format,force_format",
    [
        ("json", "pkl"),
        ("txt", "json"),
        ("yaml", "txt"),
        ("jsonl", "json"),
        ("npy", "pkl"),
        ("pkl", "json"),
    ],
)
def test_nonexistent_file_load_with_force_suffix(
    original_format, force_format, tmp_path
):
    # Generate a path that does not exist
    test_file = tmp_path / f"nonexistent_file.{original_format}"

    # Attempt to load the nonexistent file with force_suffix, expecting None as return value
    assert fu.load_file(test_file, force_suffix=force_format) is None


@pytest.mark.parametrize("file_format", ["json", "jsonl", "pkl", "txt", "npy", "yaml"])
def test_load_files(file_format, tmp_path):
    # Create multiple test files
    test_file1 = tmp_path / f"test_file1.{file_format}"
    test_file2 = tmp_path / f"test_file2.{file_format}"

    # Dump sample data to both files
    dump_file(sample_data[file_format], test_file1)
    dump_file(sample_data[file_format], test_file2)

    # Load the files using load_files
    loaded_data = load_files([test_file1, test_file2])

    # Verify that the loaded data matches the original data for both files
    if file_format == "npy":
        assert len(loaded_data) == 2
        assert np.array_equal(loaded_data[0], sample_data[file_format])
        assert np.array_equal(loaded_data[1], sample_data[file_format])
    else:
        assert len(loaded_data) == 2
        assert loaded_data[0] == sample_data[file_format]
        assert loaded_data[1] == sample_data[file_format]


@pytest.mark.parametrize("file_format", ["json", "jsonl", "pkl", "txt", "npy", "yaml"])
def test_load_files_with_nonexistent_file(file_format, tmp_path):
    # Create a valid test file and a nonexistent file
    test_file1 = tmp_path / f"test_file1.{file_format}"
    nonexistent_file = tmp_path / f"nonexistent_file.{file_format}"

    # Dump sample data to the valid file
    dump_file(sample_data[file_format], test_file1)

    # Load the files including the nonexistent one
    loaded_data = load_files([test_file1, nonexistent_file])

    # Verify the data: valid data should be loaded, None for the nonexistent file
    if file_format == "npy":
        assert len(loaded_data) == 2
        assert np.array_equal(loaded_data[0], sample_data[file_format])
        assert loaded_data[1] is None
    else:
        assert len(loaded_data) == 2
        assert loaded_data[0] == sample_data[file_format]
        assert loaded_data[1] is None
