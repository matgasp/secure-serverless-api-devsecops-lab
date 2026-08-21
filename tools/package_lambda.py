import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _write_file(archive, path, relative_path):
  info = zipfile.ZipInfo(relative_path.as_posix(), date_time=(2025, 1, 1, 0, 0, 0))
  info.compress_type = zipfile.ZIP_DEFLATED
  info.external_attr = 0o644 << 16
  archive.writestr(info, path.read_bytes())


def build(source, output, requirements, skip_dependencies=False):
  source = source.resolve()
  output = output.resolve()
  output.parent.mkdir(parents=True, exist_ok=True)

  with tempfile.TemporaryDirectory(prefix="lambda-build-") as temporary_directory:
    staging = Path(temporary_directory)
    if not skip_dependencies:
      subprocess.run(
        [
          sys.executable,
          "-m",
          "pip",
          "install",
          "--disable-pip-version-check",
          "--no-compile",
          "--requirement",
          str(requirements.resolve()),
          "--target",
          str(staging),
        ],
        check=True,
      )

    shutil.copytree(source, staging, dirs_exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
      for path in sorted(staging.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
          _write_file(archive, path, path.relative_to(staging))

  return output


def main():
  parser = argparse.ArgumentParser(description="Build a deterministic Lambda source archive")
  parser.add_argument("--source", type=Path, default=Path("src"))
  parser.add_argument("--output", type=Path, default=Path("dist/lambda.zip"))
  parser.add_argument("--requirements", type=Path, default=Path("requirements.txt"))
  parser.add_argument("--skip-dependencies", action="store_true")
  args = parser.parse_args()

  output = build(args.source, args.output, args.requirements, args.skip_dependencies)

  print(f"Created {output}")


if __name__ == "__main__":
  main()
