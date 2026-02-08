"""Test suite for Claude API."""

import unittest
import json
from backend.api import app


class TestClaudeAPI(unittest.TestCase):
    """Test cases for Claude API."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health(self):
        """Test health endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')

    def test_send_message(self):
        """Test send message endpoint."""
        response = self.client.post(
            '/message',
            json={
                'message': 'Test message',
                'context': 'Test context'
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

    def test_call_service_invalid(self):
        """Test call service with invalid format."""
        response = self.client.post(
            '/service/call',
            json={
                'service': 'invalid',
                'data': {}
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_webhook(self):
        """Test webhook endpoint."""
        response = self.client.post(
            '/webhook/test_webhook',
            json={'data': 'test'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'received')

    def test_not_found(self):
        """Test 404 error handling."""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

    def test_cors_headers(self):
        """Test CORS headers."""
        response = self.client.options('/health')
        self.assertIn('Access-Control-Allow-Origin', response.headers)


if __name__ == '__main__':
    unittest.main()
