import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_app = None


def setUpModule():
    """Aísla los ajustes en un fichero INI temporal (override de entorno).

    En macOS QSettings nativo usa CFPreferences e ignora HOME, así que la única
    forma fiable de no tocar los ajustes reales del usuario es redirigir a un
    fichero INI propio vía ILO_TUNNEL_SETTINGS_FILE.
    """
    global _app
    os.environ["ILO_TUNNEL_SETTINGS_FILE"] = os.path.join(
        tempfile.mkdtemp(), "test-settings.ini"
    )
    from PyQt6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])


class TestConnectionProfile(unittest.TestCase):
    def test_roundtrip_with_new_fields(self):
        from ilo_tunnel.models.profile import ConnectionProfile

        p = ConnectionProfile(
            name="srv",
            ilo_ip="1.2.3.4",
            ssh_user="root",
            gateway_ip="gw",
            ssh_port=2222,
            use_sudo=False,
            compress=True,
            connect_timeout=45,
            ports={"443": True, "22": False},
        )
        restored = ConnectionProfile.from_dict(p.to_dict())
        self.assertEqual(restored, p)

    def test_from_dict_defaults_for_legacy_profile(self):
        from ilo_tunnel.models.profile import ConnectionProfile

        legacy = {"name": "x", "ilo_ip": "1", "ssh_user": "u", "gateway_ip": "g"}
        p = ConnectionProfile.from_dict(legacy)
        self.assertTrue(p.use_sudo)
        self.assertTrue(p.identity_only)
        self.assertEqual(p.connect_timeout, 30)

    def test_is_valid(self):
        from ilo_tunnel.models.profile import ConnectionProfile

        self.assertFalse(ConnectionProfile("", "", "", "").is_valid())
        self.assertTrue(ConnectionProfile("n", "ip", "u", "gw").is_valid())


class TestPortMapping(unittest.TestCase):
    def test_parse_port_mapping(self):
        from ilo_tunnel.services.ssh_manager import parse_port_mapping

        self.assertEqual(
            parse_port_mapping("127.0.0.1:80:10.0.0.1:80"),
            ("127.0.0.1", 80, "10.0.0.1", 80),
        )
        self.assertIsNone(parse_port_mapping("127.0.0.1:99999:x:80"))
        self.assertIsNone(parse_port_mapping("bad"))
        self.assertIsNone(parse_port_mapping("a:b:c:d"))

    def test_build_port_mappings(self):
        from ilo_tunnel.controllers.connection_controller import build_port_mappings
        from ilo_tunnel.models.profile import ConnectionProfile

        p = ConnectionProfile(
            name="t",
            ilo_ip="10.0.0.5",
            ssh_user="u",
            gateway_ip="gw",
            local_ip="127.0.0.1",
            custom_ports=True,
            ports={"22": True, "443": True, "80": False},
        )
        self.assertEqual(
            build_port_mappings(p),
            ["127.0.0.1:22:10.0.0.5:22", "127.0.0.1:443:10.0.0.5:443"],
        )


class TestAppSettings(unittest.TestCase):
    def test_defaults_and_typing(self):
        from ilo_tunnel.app_settings import AppSettings

        s = AppSettings()
        self.assertEqual(s.get("ssh_timeout"), 30)
        self.assertIs(s.get("use_sudo"), True)
        s.set("ssh_timeout", 60)
        self.assertEqual(s.get("ssh_timeout"), 60)

    def test_unknown_key_rejected(self):
        from ilo_tunnel.app_settings import AppSettings

        with self.assertRaises(KeyError):
            AppSettings().set("inexistente", 1)


class TestServerTypes(unittest.TestCase):
    def test_user_type_lifecycle(self):
        from ilo_tunnel.models import server_types as st

        self.assertTrue(
            st.save_user_server_type("X", {22: "SSH", 8443: "Web"}, "d", [22])
        )
        self.assertIn("X", st.get_server_types())
        self.assertEqual(st.get_server_ports("X")[8443], "Web")
        self.assertEqual(st.get_server_essential_ports("X"), [22])
        self.assertFalse(st.is_builtin("X"))
        self.assertTrue(st.is_builtin("Dell"))
        # No se puede sobrescribir un predefinido
        self.assertFalse(st.save_user_server_type("Dell", {22: "SSH"}))
        self.assertTrue(st.delete_user_server_type("X"))
        self.assertNotIn("X", st.get_server_types())


if __name__ == "__main__":
    unittest.main()
