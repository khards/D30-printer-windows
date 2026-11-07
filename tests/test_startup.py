import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import startup


class StartupTests(unittest.TestCase):
    def test_install_writes_quoted_command_to_current_user_run_key(self):
        key = Mock()
        key.__enter__ = Mock(return_value=key)
        key.__exit__ = Mock(return_value=False)
        registry = SimpleNamespace(
            HKEY_CURRENT_USER="HKCU", KEY_SET_VALUE=2, REG_SZ=1,
            CreateKeyEx=Mock(return_value=key), SetValueEx=Mock(),
        )
        with patch.object(sys, "argv", ["startup.py", "install"]), \
                patch.object(startup, "__file__", r"C:\Program Files\D30\startup.py"), \
                patch.dict(sys.modules, {"winreg": registry}):
            self.assertEqual(startup.main(), 0)
        registry.SetValueEx.assert_called_once()
        args = registry.SetValueEx.call_args.args
        self.assertEqual(args[1], "D30 Print Server")
        self.assertEqual(args[4], 'wscript.exe "C:\\Program Files\\D30\\start_minimized.vbs"')

    def test_remove_deletes_only_our_entry(self):
        key = Mock()
        key.__enter__ = Mock(return_value=key)
        key.__exit__ = Mock(return_value=False)
        registry = SimpleNamespace(
            HKEY_CURRENT_USER="HKCU", KEY_SET_VALUE=2,
            CreateKeyEx=Mock(return_value=key), DeleteValue=Mock(),
        )
        with patch.object(sys, "argv", ["startup.py", "remove"]), \
                patch.dict(sys.modules, {"winreg": registry}):
            self.assertEqual(startup.main(), 0)
        registry.DeleteValue.assert_called_once_with(key, "D30 Print Server")


if __name__ == "__main__":
    unittest.main()
