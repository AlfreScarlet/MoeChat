import os
import unittest
from unittest.mock import patch

import server_settings


class NetworkDefaultsCheck(unittest.TestCase):
    def test_defaults_are_localhost_only(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(server_settings.get_web_host(), "127.0.0.1")
            self.assertEqual(server_settings.get_socket_host(), "127.0.0.1")
            self.assertEqual(
                server_settings.get_cors_origins(),
                ["http://127.0.0.1:8001", "http://localhost:8001"],
            )

    def test_remote_access_requires_explicit_environment(self):
        env = {
            "MOECHAT_HOST": "0.0.0.0",
            "MOECHAT_SOCKET_HOST": "0.0.0.0",
            "MOECHAT_CORS_ORIGINS": "http://example.local:8001, http://127.0.0.1:8001",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(server_settings.get_web_host(), "0.0.0.0")
            self.assertEqual(server_settings.get_socket_host(), "0.0.0.0")
            self.assertEqual(
                server_settings.get_cors_origins(),
                ["http://example.local:8001", "http://127.0.0.1:8001"],
            )

    def test_wildcard_cors_disables_credentials(self):
        self.assertFalse(server_settings.cors_allows_credentials(["*"]))


if __name__ == "__main__":
    unittest.main()
