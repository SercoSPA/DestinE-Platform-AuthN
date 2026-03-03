"""
Unit tests for CLI interface.

Tests command-line argument parsing, output behavior, and exit codes.
"""

import sys
import pytest
from unittest.mock import patch

from destinepyauth.cli import main
from destinepyauth.authentication import TokenResult
from destinepyauth.exceptions import AuthenticationError


class TestCLIArgumentParsing:
    """Tests for command-line argument parsing."""

    def test_cli_requires_service_argument(self):
        """Test that CLI fails when --SERVICE is not provided."""
        with patch.object(sys, "argv", ["destinepyauth"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2  # argparse error code

    def test_cli_accepts_valid_service_names(self):
        """Test that CLI accepts valid service names."""
        mock_result = TokenResult(access_token="test_token")

        with patch.object(sys, "argv", ["destinepyauth", "--SERVICE", "highway"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("highway", write_netrc=False, verbose=False)

    def test_cli_rejects_invalid_service_names(self):
        """Test that CLI rejects invalid service names."""
        with patch.object(sys, "argv", ["destinepyauth", "--SERVICE", "invalid_service"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2  # argparse error code

    def test_cli_short_flag_s_for_service(self):
        """Test that -s short flag works for service."""
        mock_result = TokenResult(access_token="test_token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "cacheb"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()

    def test_cli_verbose_flag_long(self):
        """Test that --verbose flag is passed to get_token."""
        mock_result = TokenResult(access_token="test_token")

        with patch.object(sys, "argv", ["destinepyauth", "--SERVICE", "highway", "--verbose"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("highway", write_netrc=False, verbose=True)

    def test_cli_verbose_flag_short(self):
        """Test that -v short flag works for verbose."""
        mock_result = TokenResult(access_token="test_token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway", "-v"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("highway", write_netrc=False, verbose=True)

    def test_cli_netrc_flag_long(self):
        """Test that --netrc flag is passed to get_token."""
        with patch.object(sys, "argv", ["destinepyauth", "--SERVICE", "highway", "--netrc"]):
            with patch("destinepyauth.cli.get_token", return_value=None) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("highway", write_netrc=True, verbose=False)

    def test_cli_netrc_flag_short(self):
        """Test that -n short flag works for netrc."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway", "-n"]):
            with patch("destinepyauth.cli.get_token", return_value=None) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("highway", write_netrc=True, verbose=False)

    def test_cli_multiple_flags_combined(self):
        """Test that multiple flags can be combined."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "eden", "-v", "-n"]):
            with patch("destinepyauth.cli.get_token", return_value=None) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("eden", write_netrc=True, verbose=True)


class TestCLIPrintOutput:
    """Tests for --print flag output behavior."""

    def test_cli_print_flag_outputs_token(self, capsys):
        """Test that --print outputs exactly the access token."""
        mock_result = TokenResult(
            access_token="my_secret_token_12345",
            refresh_token="refresh_token",
        )

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway", "--print"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()

        captured = capsys.readouterr()
        assert captured.out == "my_secret_token_12345\n"
        assert captured.err == ""

    def test_cli_print_short_flag_outputs_token(self, capsys):
        """Test that -p short flag outputs the access token."""
        mock_result = TokenResult(access_token="another_token_xyz")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "cacheb", "-p"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()

        captured = capsys.readouterr()
        assert captured.out == "another_token_xyz\n"

    def test_cli_without_print_no_output(self, capsys):
        """Test that without --print, no token is output."""
        mock_result = TokenResult(access_token="secret_token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                main()

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_cli_print_with_netrc_handles_none_result(self, capsys):
        """Test that --print with --netrc exits with error when result is None."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway", "--netrc", "--print"]):
            with patch("destinepyauth.cli.get_token", return_value=None):
                # The CLI has a bug - it doesn't handle write_netrc properly with --print
                # It should either prevent this combination or handle None result gracefully
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2


class TestCLIExitCodes:
    """Tests for CLI exit codes."""

    def test_cli_exits_0_on_success(self):
        """Test that CLI exits with code 0 on success."""
        mock_result = TokenResult(access_token="token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result):
                # Should not raise SystemExit
                main()

    def test_cli_exits_1_on_authentication_error(self):
        """Test that CLI exits with code 1 on AuthenticationError."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch(
                "destinepyauth.cli.get_token",
                side_effect=AuthenticationError("Auth failed"),
            ):
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

    def test_cli_exits_1_on_unexpected_exception(self):
        """Test that CLI exits with code 1 on unexpected exceptions."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch(
                "destinepyauth.cli.get_token",
                side_effect=RuntimeError("Unexpected error"),
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1


class TestCLIErrorMessages:
    """Tests for CLI error message logging."""

    def test_cli_logs_authentication_error_message(self, caplog):
        """Test that AuthenticationError message is logged."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch(
                "destinepyauth.cli.get_token",
                side_effect=AuthenticationError("Invalid credentials"),
            ):
                with pytest.raises(SystemExit):
                    main()

        assert "Invalid credentials" in caplog.text

    def test_cli_logs_keyboard_interrupt_message(self, caplog):
        """Test that KeyboardInterrupt logs cancellation message."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", side_effect=KeyboardInterrupt()):
                with pytest.raises(SystemExit):
                    main()

        assert "Authentication cancelled" in caplog.text

    def test_cli_logs_unexpected_error_message(self, caplog):
        """Test that unexpected errors are logged."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch(
                "destinepyauth.cli.get_token",
                side_effect=RuntimeError("Something went wrong"),
            ):
                with pytest.raises(SystemExit):
                    main()

        assert "Unexpected error: Something went wrong" in caplog.text


class TestCLINetrcBehavior:
    """Tests for --netrc flag behavior."""

    def test_cli_netrc_calls_get_token_with_write_netrc_true(self):
        """Test that --netrc passes write_netrc=True to get_token."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway", "--netrc"]):
            with patch("destinepyauth.cli.get_token", return_value=None) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("highway", write_netrc=True, verbose=False)

    def test_cli_without_netrc_calls_get_token_with_write_netrc_false(self):
        """Test that without --netrc, write_netrc=False is passed."""
        mock_result = TokenResult(access_token="token")

        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway"]):
            with patch("destinepyauth.cli.get_token", return_value=mock_result) as mock_get_token:
                main()
                mock_get_token.assert_called_once_with("highway", write_netrc=False, verbose=False)

    def test_cli_netrc_succeeds_without_print(self, capsys):
        """Test that --netrc works without --print and produces no output."""
        with patch.object(sys, "argv", ["destinepyauth", "-s", "highway", "--netrc"]):
            with patch("destinepyauth.cli.get_token", return_value=None):
                main()

        captured = capsys.readouterr()
        assert captured.out == ""
