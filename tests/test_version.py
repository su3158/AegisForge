from aegisforge import __version__
from aegisforge.cli import main


def test_version_constant():
    assert __version__ == "0.2.0-alpha"


def test_version_command(capsys):
    assert main(["version"]) == 0
    assert "0.2.0-alpha" in capsys.readouterr().out
