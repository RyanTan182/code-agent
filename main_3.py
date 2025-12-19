"""
NOT USED
Allows senior developer to upload folders/Github Link to provide
- Documentation of codebase
- Onboarding Forms for Junior Devs/Intern to get started
- Allows users to ask questions on what certain files do 
& even provide files on where to work on when user tells them their feature that they have to develop

Senior Developer can provide one of the following
    1. Github Repo Link
    - Checks whether it is accessible through checking whether it is public repo or a private repo
    - If it is private, show them a notice 
    - If it is public, they can do the following

    2. Folder Upload
    - Checks through contents of the folder, every text file and every coding file included 
    and do the following
 """

import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict

from connectonion import Agent, xray
from playwright.sync_api import sync_playwright

DEFAULT_CLONE_ROOT = Path("repos")

class GithubAccessLink:
    """If user uploads a Github Repo URL link, check GitHub accessibility and optionally clone."""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.clone_root = DEFAULT_CLONE_ROOT
        self.clone_root.mkdir(parents=True, exist_ok=True)

    def start_browser(self, headless: bool = False) -> str:
        """Start a new browser instance"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        return "Browser started successfully"

    def set_clone_root(self, root: Path | str):
        self.clone_root = Path(root)
        self.clone_root.mkdir(parents=True, exist_ok=True)
        return f"Clone root set to {self.clone_root}"

    def navigate(self, github_url: str, clone_on_success: bool = False, dest_root: Path | str | None = None) -> str:
        if not self.page:
            self.start_browser(headless=True)
        response = self.page.goto(github_url, wait_until="domcontentloaded")
        status = response.status if response else None
        body_text = self.page.inner_text("body")

        if status == 404:
            return "Repository not found! Please link a valid public Github Repository."
        if status == 401:
            return "Private Repo or not Authorized. Please link a valid public Github Repository."
        
        text_lower = body_text.lower()
        if "this repository is private" in text_lower:
            return "Repository is private (visible banner)."
        if "repository unavailable" in text_lower or "not found" in text_lower:
            return "Repository not accessible."

        accessible_msg = f"Repository accessible (status {status})."
        if not clone_on_success:
            return accessible_msg

        clone_result = self.clone_public_repo(github_url, dest_root)
        return f"{accessible_msg}\n{clone_result}"

    def clone_public_repo(self, github_url: str, dest_root: Path | str | None = None) -> str:
        """
        Clone a public GitHub repo into /repos
        """
        repo_name = github_url.rstrip("/").split("/")[-1] or "repo"
        root = Path(dest_root) if dest_root else self.clone_root
        destination = root / repo_name
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            return f"Destination {destination} already exists. Remove it or choose another folder."

        result = subprocess.run(
            ["git", "clone", "--depth", "1", github_url, str(destination)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"Failed to clone repo (code {result.returncode}): {result.stderr.strip()}"

        return f"Cloned to {destination}"

    def close_browser(self) -> str:
        """Close the browser and clean up"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        return "Browser closed"

DOCS_ROOT = Path("docs")


class APIDocumentation:
    """Scan a cloned repo and write API endpoint docs under ./docs."""

    def __init__(self, docs_root: Path = DOCS_ROOT):
        self.docs_root = docs_root
        self.docs_root.mkdir(parents=True, exist_ok=True)
        self.route_patterns = [
            re.compile(r"@(app|api|router)\.(get|post|put|patch|delete|options|head)\(\s*[\"']([^\"']+)", re.IGNORECASE),
            re.compile(r"@.*route\(\s*[\"']([^\"']+)", re.IGNORECASE),
            re.compile(r"\b(app|router)\.(get|post|put|patch|delete|options|head)\(\s*[\"']([^\"']+)", re.IGNORECASE),
            re.compile(r"\bpath\(\s*[\"']([^\"']+)", re.IGNORECASE),
            re.compile(r"\bre_path\(\s*[\"']([^\"']+)", re.IGNORECASE),
        ]
        self.allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx"}

    def scan_api_endpoints(self, repo_root: Path) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        if not repo_root.exists():
            return entries
        for file_path in repo_root.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in self.allowed_exts:
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines():
                for pattern in self.route_patterns:
                    match = pattern.search(line)
                    if not match:
                        continue
                    method = "GET"
                    route = ""
                    if len(match.groups()) == 3:
                        method = match.group(2).upper()
                        route = match.group(3)
                    else:
                        route = match.group(match.lastindex or 1)
                    entries.append(
                        {
                            "method": method,
                            "path": route,
                            "file": str(file_path.relative_to(repo_root)),
                            "line": line.strip()[:200],
                        }
                    )
                    break
        return entries

    def write_markdown(self, repo_root: Path, entries: List[Dict[str, str]]) -> Path:
        repo_name = repo_root.name
        doc_path = self.docs_root / f"{repo_name}_api.md"
        header = [
            f"# API Documentation for {repo_name}",
            f"Repo path: {repo_root}",
            "",
            "## Endpoints",
        ]
        if not entries:
            body = ["No endpoints detected."]
        else:
            body = ["| Method | Path | File | Notes |", "| --- | --- | --- | --- |"]
            for item in entries:
                body.append(
                    f"| {item['method']} | {item['path']} | {item['file']} | {item['line']} |"
                )
        doc_path.write_text("\n".join(header + body), encoding="utf-8")
        return doc_path

    def document_repo(self, repo_root: Path) -> str:
        entries = self.scan_api_endpoints(repo_root)
        doc_path = self.write_markdown(repo_root, entries)
        return f"Documented {len(entries)} endpoint(s) to {doc_path}"

github = GithubAccessLink()
github.start_browser(headless=False)
api_doc = APIDocumentation()

agent = Agent(
    "API documentation and Onboarding form",
    tools=[github, api_doc],
    system_prompt="Help me check whether a given GitHub repo link is public or private, clone public repos into ./repos, and document detected API endpoints into ./docs.",
)

if __name__ == "__main__":
    use_agent = "--agent" in sys.argv[1:]
    args = [a for a in sys.argv[1:] if a != "--agent"]
    repo_url = args[0] if args else input("GitHub repo URL: ").strip()
    if not repo_url:
        print("Provide a GitHub repo URL.")
    elif use_agent:
        prompt = f"Inspect {repo_url} to check access, clone if public, and document API endpoints."
        agent.auto_debug(max_steps=10)
        print(agent.input(prompt))
    else:
        clone_msg = github.clone_public_repo(repo_url)
        print(clone_msg)
        repo_name = repo_url.rstrip("/").split("/")[-1] or "repo"
        repo_path = github.clone_root / repo_name
        print(api_doc.document_repo(repo_path))