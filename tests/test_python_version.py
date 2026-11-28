import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent


class PythonVersionTests(unittest.TestCase):
    def test_python_minor_is_the_same_everywhere(self):
        # A Renovate "Python version" PR can open with only some of the files: keep it red until all move.
        config = json.loads((ROOT / "renovate.json").read_text())
        [manager] = [m for m in config["customManagers"] if m.get("depNameTemplate") == "python"]
        header = manager["matchStrings"][0].replace("(?<", "(?P<")  # JS -> Python groups
        found = [re.search(header, (ROOT / "requirements.lock").read_text())["currentValue"]]
        found += re.findall(r"^FROM python:(\d+\.\d+)-slim", (ROOT / "Dockerfile").read_text(), re.M)
        found += re.findall(r"python-version: '(\d+\.\d+)'", (ROOT / ".github/workflows/test.yml").read_text())
        self.assertEqual(len(found), 4, found)
        self.assertEqual(len(set(found)), 1, found)
