import os
import subprocess


def get_version() -> str:
    """Fetches app current build number and branch name (from local Git repository)"""
    if ".git" in os.listdir("."):
        try:
            build_num = subprocess.check_output("git rev-list --count HEAD", shell=True).decode("utf-8").strip()
            branch_name = subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True).decode("utf-8").strip()
            return f"build {build_num} ({branch_name})"
        except subprocess.CalledProcessError:
            return "unknown (not Git?)"
    else:
        return "unknown"
