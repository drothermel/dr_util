import dr_util.file_utils as fu


def test_help(capfd):
    helps = fu.help_str()
    assert helps != ''
