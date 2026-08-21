import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".json", ".md", ".mjs", ".py", ".tf", ".txt", ".yaml", ".yml"}
EXCLUDED_PARTS = {
  ".git",
  ".terraform",
  ".venv",
  "dist",
  "node_modules",
  "reports",
  "__pycache__",
}
SKIP_FILES = {Path(__file__).resolve()}

SECRET_PATTERNS = {
  "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
  "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
  "Private key": re.compile("-----BEGIN " + "(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
  "Hard-coded credential": re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"${}]{8,}['\"]"
  ),
}

UNSAFE_PATTERNS = {
  "dynamic code execution": re.compile(r"\b(?:eval|exec)\s*\("),
  "disabled TLS verification": re.compile(r"verify\s*=\s*False"),
  "shell execution": re.compile(r"shell\s*=\s*True"),
}


def source_files():
  for path in ROOT.rglob("*"):
    if path.is_file() and path.suffix in EXTENSIONS:
      if path.resolve() in SKIP_FILES or any(part in EXCLUDED_PARTS for part in path.parts):
        continue

      yield path


def main():
  findings = []

  for path in source_files():
    text = path.read_text(encoding="utf-8", errors="replace")
    for category, pattern in {**SECRET_PATTERNS, **UNSAFE_PATTERNS}.items():
      for match in pattern.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        findings.append(f"{path.relative_to(ROOT)}:{line}: {category}")

  if findings:
    print("Security checks failed:")
    print("\n".join(findings))
    return 1

  print("Security checks passed: no known secret or unsafe-code patterns found.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
