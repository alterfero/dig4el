"""Exercise admin helpers without authentication, network calls, or real storage."""
import ast
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

PAGE = Path(__file__).resolve().parents[1] / "pages" / "File_explorer.py"
TREE = ast.parse(PAGE.read_text())
HELPERS = {
    node.name: ast.unparse(node)
    for node in TREE.body
    if isinstance(node, ast.FunctionDef)
}


class Session(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class LanguageDeletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "Test" / "nested").mkdir(parents=True)
        (self.root / "Test" / "nested" / "data.txt").write_text("data")
        self.registry = self.root / "languages.json"
        self.registry.write_text(json.dumps({"Test": "test1234", "Other": "othe1234"}))
        self.session = Session(current_path=str(self.root / "Test" / "nested"),
                               l_with_data=["Test", "Other"], empty_language_scan=["Test"])
        self.gu = SimpleNamespace(GLOTTO_LANGUAGE_LIST={"Test": "test1234"}, LLIST=["Test"])
        self.env = dict(Path=Path, Any=object, json=json, os=os, shutil=shutil,
                        tempfile=tempfile, ROOT_PATH=self.root, gu=self.gu,
                        st=SimpleNamespace(session_state=self.session))
        names = ["ensure_path_within_root", "atomic_write_text", "atomic_write_json",
                 "load_json_file", "delete_directory_safe", "delete_language_workspace"]
        exec("\n\n".join(HELPERS[name] for name in names), self.env)

    def test_removes_workspace_registry_and_cached_lists(self):
        self.env["delete_language_workspace"]("Test")
        self.assertFalse((self.root / "Test").exists())
        self.assertEqual(json.loads(self.registry.read_text()), {"Other": "othe1234"})
        self.assertEqual(self.gu.GLOTTO_LANGUAGE_LIST, {"Other": "othe1234"})
        self.assertEqual(self.gu.LLIST, ["Other"])
        self.assertEqual(self.session.llist, ["Other"])
        self.assertEqual(self.session.l_with_data, ["Other"])
        self.assertEqual(self.session.current_path, str(self.root))
        self.assertIsNone(self.session.empty_language_scan)

    def test_registry_write_failure_preserves_workspace(self):
        self.env["atomic_write_json"] = Mock(side_effect=PermissionError("read only"))
        with self.assertRaises(PermissionError):
            self.env["delete_language_workspace"]("Test")
        self.assertTrue((self.root / "Test" / "nested" / "data.txt").exists())
        self.assertIn("Test", json.loads(self.registry.read_text()))

    def test_failed_deletion_restores_registry(self):
        self.env["delete_directory_safe"] = Mock(side_effect=PermissionError("denied"))
        with self.assertRaises(PermissionError):
            self.env["delete_language_workspace"]("Test")
        self.assertIn("Test", json.loads(self.registry.read_text()))
        self.assertIn("Test", self.gu.LLIST)

    def test_rejects_root_nested_paths_and_symlinks(self):
        (self.root / "Alias").symlink_to(self.root / "Test", target_is_directory=True)
        for language in [".", "../outside", "Test/nested", "Alias"]:
            with self.subTest(language=language), self.assertRaises(ValueError):
                self.env["delete_language_workspace"](language)
        self.assertTrue((self.root / "Test").exists())

    def test_unregistered_workspace_can_be_deleted(self):
        self.registry.write_text('{"Other": "othe1234"}')
        self.env["delete_language_workspace"]("Test")
        self.assertEqual(json.loads(self.registry.read_text()), {"Other": "othe1234"})

    def test_invalid_registry_preserves_workspace(self):
        self.registry.write_text('[]')
        with self.assertRaises(ValueError):
            self.env["delete_language_workspace"]("Test")
        self.assertTrue((self.root / "Test").exists())


class ConfirmationTests(unittest.TestCase):
    def test_form_accepts_exact_phrase_and_rejects_blank_or_wrong_phrase(self):
        app = AppTest.from_string(
            "import streamlit as st\n" + HELPERS["confirmed_form_submit"] + '''
with st.form("delete"):
    phrase = st.text_input("Confirmation")
    confirmed = confirmed_form_submit("Delete workspace", phrase, "DELETE Test")
if confirmed:
    st.success("Deletion invoked")
'''
        ).run()
        self.assertFalse(app.button[0].disabled)
        app.button[0].click().run()
        self.assertEqual(len(app.error), 1)
        self.assertEqual(len(app.success), 0)
        app.text_input[0].input("DELETE Other")
        app.button[0].click().run()
        self.assertEqual(len(app.error), 1)
        self.assertEqual(len(app.success), 0)
        app.text_input[0].input("DELETE Test")
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.success), 1)

    def test_all_maintenance_forms_validate_on_submit(self):
        calls = [node for node in ast.walk(TREE) if isinstance(node, ast.Call)]
        confirmation_calls = [node for node in calls if isinstance(node.func, ast.Name)
                              and node.func.id == "confirmed_form_submit"]
        self.assertEqual(len(confirmation_calls), 4)
        deletion_calls = [node for node in calls if isinstance(node.func, ast.Name)
                          and node.func.id == "delete_language_workspace"]
        self.assertEqual(len(deletion_calls), 2)


if __name__ == "__main__":
    unittest.main()
