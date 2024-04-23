import dr_utils.file_utils as fu


def test_help():
    fu.help()
    stdout, stderr = capsys.readouterr()
    assert stdout != ""
