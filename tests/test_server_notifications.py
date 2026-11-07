import unittest
from unittest.mock import Mock, patch

import serial

import server
from d30.discovery import PortResolutionError


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        self.notify = Mock()
        server.app.config["PRINT_ERROR_CALLBACK"] = self.notify

    def tearDown(self):
        server.app.config.pop("PRINT_ERROR_CALLBACK", None)

    def test_missing_printer_notifies_and_preserves_http_error(self):
        with patch.object(server.jobs, "print_text", side_effect=PortResolutionError("No D30 port")):
            response = self.client.post("/api/print", json={"text": "test"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json(), {"status": "error", "message": "No D30 port"})
        self.assertIn("pairing", self.notify.call_args.args[0])

    def test_serial_error_notifies_user(self):
        with patch.object(server.jobs, "print_text", side_effect=serial.SerialException("port unavailable")):
            response = self.client.post("/api/print", json={"text": "test"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("port unavailable", response.get_json()["message"])
        self.assertIn("on and paired", self.notify.call_args.args[0])

    def test_bad_request_notifies_user(self):
        response = self.client.post("/api/print", json={})
        self.assertEqual(response.status_code, 400)
        self.notify.assert_called_once()

    def test_success_and_options_do_not_notify(self):
        with patch.object(server.jobs, "print_text", return_value="COM5"):
            response = self.client.post("/api/print", json={"text": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["com_port"], "COM5")
        self.assertEqual(self.client.options("/api/print").status_code, 204)
        self.notify.assert_not_called()

    def test_failed_notification_does_not_change_api_response(self):
        self.notify.side_effect = RuntimeError("notification failed")
        response = self.client.post("/api/print", json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], "error")


if __name__ == "__main__":
    unittest.main()
