"""
Unit tests for exception handling and error utilities.

Tests AuthenticationError, handle_http_errors decorator, and error handling.
"""

import pytest
from unittest.mock import MagicMock

from destinepyauth.exceptions import AuthenticationError, handle_http_errors


class TestAuthenticationError:
    """Tests for exception handling."""

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError."""
        error = AuthenticationError("Test error message")
        assert str(error) == "Test error message"

    def test_authentication_error_is_exception(self):
        """Test that AuthenticationError is an Exception."""
        assert issubclass(AuthenticationError, Exception)


class TestHandleHttpErrorsDecorator:
    """Tests for HTTP error handling decorator."""

    def test_handle_http_errors_successful_call(self):
        """Test that successful function calls pass through."""

        @handle_http_errors("Test error")
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"

    def test_handle_http_errors_timeout(self):
        """Test that timeout is caught and converted to AuthenticationError."""
        import requests

        @handle_http_errors("Failed to connect")
        def timeout_func():
            raise requests.Timeout("Connection timed out")

        with pytest.raises(AuthenticationError, match="Failed to connect: Connection timeout"):
            timeout_func()

    def test_handle_http_errors_connection_error(self):
        """Test that ConnectionError is caught and converted."""
        import requests

        @handle_http_errors("Failed to connect")
        def connection_func():
            raise requests.ConnectionError("Connection refused")

        with pytest.raises(AuthenticationError, match="Failed to connect: Connection failed"):
            connection_func()

    def test_handle_http_errors_http_error(self):
        """Test that HTTPError is caught and converted."""
        import requests

        @handle_http_errors("Request failed")
        def http_error_func():
            response = MagicMock()
            response.status_code = 401
            raise requests.HTTPError("Unauthorized", response=response)

        with pytest.raises(AuthenticationError, match="Request failed: HTTP 401"):
            http_error_func()

    def test_handle_http_errors_generic_request_exception(self):
        """Test that RequestException is caught and converted."""
        import requests

        @handle_http_errors("Request failed")
        def request_error_func():
            raise requests.RequestException("Generic request error")

        with pytest.raises(AuthenticationError, match="Request failed: Generic request error"):
            request_error_func()
