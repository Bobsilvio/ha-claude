"""Tests for services/auth_service.py"""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAuthService(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.tmpdir, "settings.json")
        # Patch the settings file path + clear module cache between tests
        import services.auth_service as auth_mod
        self._orig_settings = auth_mod._SETTINGS_FILE
        auth_mod._SETTINGS_FILE = self.settings_file
        auth_mod._cached_token = None

    def tearDown(self):
        import services.auth_service as auth_mod
        auth_mod._SETTINGS_FILE = self._orig_settings
        auth_mod._cached_token = None

    def test_token_generated_on_first_call(self):
        import services.auth_service as auth_mod
        token = auth_mod.get_or_create_token()
        self.assertTrue(len(token) > 20)
        # Persisted to disk
        with open(self.settings_file) as f:
            saved = json.load(f)
        self.assertEqual(saved["amira_api_token"], token)

    def test_token_idempotent(self):
        import services.auth_service as auth_mod
        t1 = auth_mod.get_or_create_token()
        auth_mod._cached_token = None  # clear cache to force re-read
        t2 = auth_mod.get_or_create_token()
        self.assertEqual(t1, t2)

    def test_validate_token_correct(self):
        import services.auth_service as auth_mod
        with patch.object(auth_mod, "_AUTH_ENFORCED", True):
            token = auth_mod.get_or_create_token()
            self.assertTrue(auth_mod.validate_token(token))

    def test_validate_token_wrong(self):
        import services.auth_service as auth_mod
        with patch.object(auth_mod, "_AUTH_ENFORCED", True):
            auth_mod.get_or_create_token()
            self.assertFalse(auth_mod.validate_token("wrong-token"))

    def test_validate_token_empty(self):
        import services.auth_service as auth_mod
        with patch.object(auth_mod, "_AUTH_ENFORCED", True):
            auth_mod.get_or_create_token()
            self.assertFalse(auth_mod.validate_token(None))
            self.assertFalse(auth_mod.validate_token(""))

    def test_validate_token_bypass_when_not_enforced(self):
        import services.auth_service as auth_mod
        with patch.object(auth_mod, "_AUTH_ENFORCED", False):
            self.assertTrue(auth_mod.validate_token(None))
            self.assertTrue(auth_mod.validate_token("garbage"))

    def test_validate_token_open_if_no_stored_token(self):
        """If no token stored yet, allow access (migration path for existing installs)."""
        import services.auth_service as auth_mod
        with patch.object(auth_mod, "_AUTH_ENFORCED", True):
            # Don't call get_or_create_token — no token stored
            self.assertTrue(auth_mod.validate_token("any"))

    def test_is_ingress_request_true(self):
        import services.auth_service as auth_mod
        req = MagicMock()
        req.headers = {"X-Ingress-Path": "/api/hassio_ingress/abc123"}
        self.assertTrue(auth_mod.is_ingress_request(req))

    def test_is_ingress_request_false(self):
        import services.auth_service as auth_mod
        req = MagicMock()
        req.headers.get = lambda k, d=None: None
        self.assertFalse(auth_mod.is_ingress_request(req))

    def test_is_exempt_path(self):
        import services.auth_service as auth_mod
        self.assertTrue(auth_mod.is_exempt_path("/api/whatsapp/webhook"))
        self.assertFalse(auth_mod.is_exempt_path("/api/settings"))
        self.assertFalse(auth_mod.is_exempt_path("/api/telegram/message"))

    def test_invalidate_cache(self):
        import services.auth_service as auth_mod
        auth_mod.get_or_create_token()
        self.assertIsNotNone(auth_mod._cached_token)
        auth_mod.invalidate_cache()
        self.assertIsNone(auth_mod._cached_token)


if __name__ == "__main__":
    unittest.main(verbosity=2)
