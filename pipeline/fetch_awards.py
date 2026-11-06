"""Download the nominations file from DLu/oscar_data at a pinned commit.

Upstream names it oscars.csv, but it is tab-separated, so it is stored as .tsv.
To take a new upstream release, change SOURCE_COMMIT and SOURCE_SHA256 together.
"""
import hashlib
import urllib.request

from common import AWARDS_FILE, ROOT

SOURCE_COMMIT = "c5e9716b7e020e70205d6b95f5a5678526c1b45f"
SOURCE_SHA256 = "3b1d39eedad7303468b83323f51bd1069289a2710ff9873efc4b4298ae1bba78"
SOURCE_URL = f"https://raw.githubusercontent.com/DLu/oscar_data/{SOURCE_COMMIT}/oscars.csv"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def run():
    if AWARDS_FILE.exists():
        data = AWARDS_FILE.read_bytes()
    else:
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "every-envelope-pipeline"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        AWARDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        AWARDS_FILE.write_bytes(data)
        print(f"  downloaded {AWARDS_FILE.relative_to(ROOT)}")

    digest = sha256(data)
    if digest != SOURCE_SHA256:
        raise SystemExit(f"Awards file hash mismatch: expected {SOURCE_SHA256}, got {digest}")
    print(f"  awards file verified at commit {SOURCE_COMMIT[:7]}")


if __name__ == "__main__":
    run()
