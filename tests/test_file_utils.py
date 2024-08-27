import dr_util.file_utils as fu


def test_help():
    helps = fu.help_str()
    assert helps != ""
