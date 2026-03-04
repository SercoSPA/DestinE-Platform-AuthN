"""
Unit tests for CLI interface.

Tests command-line argument parsing, output, and exit codes.
"""

import sys
import pytest
from unittest.mock import patch

from destinepyauth.cli import main
from destinepyauth.authentication import TokenResult
from destinepyauth.exceptions import AuthenticationError


class TestCLIBasics:
    """Core CLI functionality tests."""

    def test_cli_requires_service_argument(self):
        """Test that CLI fails when --SERVICE is not provided."""
        with patch.object(sys, "argv", ["destinepyauth"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_cli_rejects_invalid_service_names(self):
        """Test that CLI rejects invalid service names."""
        with patch.object(sys, "argv", ["destinepyauth", "--SERVICE", "invalid_service"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_cli_accepts_valid_service(self):
        """Test that CLI accepts valid service names and calls get_token."""
        mock_result = TokenResult(access_token="test_token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()  # Should not raise

    def test_cli_passes_flags_to_get_token(self):
        """Test that CLI flags are passed correctly to get_token."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "eden", "-v", "-n"]):
            with patch("destinepyauth.cli.get_token", return_value=None) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("eden", write_netrc=True, verbose=True)


class TestCLIPrintOutput:
    """Tests for --print flag output."""

    def test_cli_print_outputs_token(self, capsys):
        """Test that --print outputs exactly the access token."""
        mock_result = TokenResult(access_token="my_secret_token_12345")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway", "--print"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()

        captured = capsys.readouterr()
        assert captured.out == "my_secret_token_12345\n"

    def test_cli_without_print_no_output(self, capsys):
        """Test that without --print, no token is output."""
        mock_result = TokenResult(access_token="secret_token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()

        captured = capsys.readouterr()
        assert captured.out == ""


class TestCLIExitCodes:
    """Tests for CLI exit codes."""

    def test_cli_exits_0_on_success(self):
        """Test that CLI exits with code 0 on success."""
        mock_result = TokenResult(access_token="token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()  # Should not raise SystemExit

    def test_cli_exits_1_on_authentication_error(self):
        """Test that CLI exits with code 1 on AuthenticationError."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", side_effect=AuthenticationError("Auth failed")):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_cli_exits_130_on_keyboard_interrupt(self):
        """Test that CLI exits with code 130 on KeyboardInterrupt."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", side_effect=KeyboardInterrupt()):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 130


class TestCLIErrorLogging:
    """Tests that errors are logged appropriately."""

    def test_cli_logs_authentication_error(self, caplog):
        """Test that AuthenticationError message is logged."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", side_effect=AuthenticationError("Invalid credentials")):
                with pytest.raises(SystemExit):
                    main()

        assert "Invalid credentials" in caplog.text
