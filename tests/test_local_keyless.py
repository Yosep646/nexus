"""Authentication boundary: keyless loopback only when explicitly enabled."""
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from backend.security import require_api_key


def request_from(host):
    request = Mock()
    request.client.host = host
    return request


def test_local_loopback_without_key():
    with patch.dict("os.environ", {"NEXUS_LOCAL_NO_AUTH": "true"}, clear=True):
        assert require_api_key(request_from("127.0.0.1"), None) is None


def test_nonlocal_request_cannot_bypass_auth():
    with patch.dict("os.environ", {"NEXUS_LOCAL_NO_AUTH": "true"}, clear=True):
        with pytest.raises(HTTPException) as error:
            require_api_key(request_from("192.168.1.30"), None)
        assert error.value.status_code == 503


def test_loopback_still_protected_when_disabled():
    with patch.dict("os.environ", {"NEXUS_LOCAL_NO_AUTH": "false"}, clear=True):
        with pytest.raises(HTTPException) as error:
            require_api_key(request_from("127.0.0.1"), None)
        assert error.value.status_code == 503
