#!/usr/bin/env python3
"""Deploy screener output to GitHub Pages (gh-pages branch)."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)


def deploy():
    """Deploy output/ contents to the gh-pages branch."""
    output_dir = Path("output")
    if not output_dir.exists() or not (output_dir / "index.html").exists():
        print("Error: No output/index.html found. Run main.py first.")
        sys.exit(1)

    # Ensure GITHUB_PUSH_TOKEN is available
    token = os.environ.get("GITHUB_PUSH_TOKEN")
    if not token:
        print("Error: GITHUB_PUSH_TOKEN not set. Run: source .env && export GITHUB_PUSH_TOKEN")
        sys.exit(1)

    # Get repo URL with token
    result = run("git remote get-url origin", check=False)
    remote_url = result.stdout.strip()
    if "github.com" in remote_url:
        # Convert to https with token
        if remote_url.startswith("git@"):
            remote_url = remote_url.replace("git@github.com:", "https://github.com/")
        if not remote_url.startswith("https://"):
            remote_url = f"https://github.com/{remote_url}"
        auth_url = remote_url.replace("https://", f"https://x-access-token:{token}@")
    else:
        auth_url = remote_url

    # Create temp directory for gh-pages
    tmp_dir = Path("/tmp/gh-pages-deploy")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir()

    # Copy output files
    for f in output_dir.iterdir():
        dest = tmp_dir / f.name
        if f.is_dir():
            shutil.copytree(f, dest)
        else:
            shutil.copy2(f, dest)

    # Initialize git in temp dir and push to gh-pages
    os.chdir(tmp_dir)
    run("git init")
    run("git config commit.gpgsign false")
    run("git checkout -b gh-pages")
    run("git add -A")
    run('git commit -m "Deploy screener results"')

    # Force push to gh-pages
    max_retries = 4
    for attempt in range(max_retries):
        result = run(f"git push -f {auth_url} gh-pages", check=False)
        if result.returncode == 0:
            print("\nDeployed to GitHub Pages successfully!")
            print("View at: https://richacarson.github.io/Stock-Screener/")
            break
        else:
            if attempt < max_retries - 1:
                import time
                wait = 2 ** (attempt + 1)
                print(f"  Push failed, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"Error: Push failed after {max_retries} attempts")
                print(result.stderr)
                sys.exit(1)

    # Cleanup
    os.chdir(Path(__file__).parent.parent)
    shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    deploy()
