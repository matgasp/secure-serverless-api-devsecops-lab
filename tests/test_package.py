import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from package_lambda import build  # noqa: E402


class PackageTests(unittest.TestCase):
  def test_source_only_package_contains_handler(self):
    with tempfile.TemporaryDirectory() as directory:
      output = Path(directory) / "lambda.zip"
      build(ROOT / "src", output, ROOT / "requirements.txt", skip_dependencies=True)

      with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        self.assertIn("app.py", names)
        self.assertIn("secure_api/handler.py", names)
        self.assertNotIn("__pycache__", "\n".join(names))


if __name__ == "__main__":
  unittest.main()
