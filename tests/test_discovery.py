import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from d30 import discovery


class RegistryKey:
    def __init__(self, children=None, values=None):
        self.children = children or {}
        self.values = values or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def registry(devices):
    root = RegistryKey({
        "Dev_" + address: RegistryKey({"instance": RegistryKey(values={"FriendlyName": name})})
        for address, name in devices.items()
    })

    def open_key(key, name):
        if key == "HKLM":
            return root
        return key.children[name]

    return SimpleNamespace(
        HKEY_LOCAL_MACHINE="HKLM",
        OpenKey=open_key,
        QueryInfoKey=lambda key: (len(key.children), 0, 0),
        EnumKey=lambda key, index: list(key.children)[index],
        QueryValueEx=lambda key, name: (key.values[name], 1),
    )


def port(device, address, suffix="C00000000"):
    return SimpleNamespace(
        device=device,
        hwid=(
            r"BTHENUM\{00001101-0000-1000-8000-00805F9B34FB}_LOCALMFG&0002"
            + "\\7&123&0&" + address + "_" + suffix
        ),
    )


class DiscoveryTests(unittest.TestCase):
    def detect(self, devices, ports):
        with patch.object(discovery.sys, "platform", "win32"), \
                patch.dict(sys.modules, {"winreg": registry(devices)}), \
                patch.object(discovery.list_ports, "comports", return_value=ports):
            return discovery.resolve_port(None)

    def test_selects_only_the_outgoing_port_for_the_named_device(self):
        ports = [
            port("COM4", "000000000000", "00000002"),
            port("COM5", "AABBCCDDEEFF"),
            port("COM6", "112233445566"),
            SimpleNamespace(device="COM7", hwid="USB"),
        ]
        self.assertEqual(self.detect({"AABBCCDDEEFF": "D30", "112233445566": "Other"}, ports), "COM5")

    def test_missing_port_is_an_error(self):
        with self.assertRaisesRegex(discovery.PortResolutionError, "No outgoing"):
            self.detect({"AABBCCDDEEFF": "D30"}, [port("COM4", "000000000000", "00000002")])

    def test_multiple_matching_ports_are_an_error(self):
        with self.assertRaisesRegex(discovery.PortResolutionError, "Multiple outgoing"):
            self.detect({"AABBCCDDEEFF": "D30"}, [port("COM5", "AABBCCDDEEFF"), port("COM6", "AABBCCDDEEFF")])

    def test_explicit_port_skips_discovery(self):
        with patch.object(discovery, "_windows_d30_ports", side_effect=AssertionError):
            self.assertEqual(discovery.resolve_port("COM9"), "COM9")


if __name__ == "__main__":
    unittest.main()
