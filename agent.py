"""
Codebase Assistant TUI - Clone repos, and analyze codebase, from explaining how certain files work and provide  for junior developers.
"""

import subprocess
from pathlib import Path
from typing import List
import requests

from connectonion import Agent, xray
from connectonion.tui import Input, pick, fuzzy_match, highlight_match

DEFAULT_CLONE_ROOT = Path("repos")


class GithubAccessLink:
    """If user uploads a Github Repo URL link, check GitHub accessibility and optionally clone to /repos"""
    
    def __init__(self, root: Path | str = DEFAULT_CLONE_ROOT):
        """Initialize with clone root directory."""
        self.set_clone_root(root)
    
    @xray
    def set_clone_root(self, root: Path | str = DEFAULT_CLONE_ROOT) -> str:
        """
        Create directory "/repos" and clones repositories into it        
        """
        self.clone_root = Path(root)
        self.clone_root.mkdir(parents=True, exist_ok=True)
        return f"Clone root set to {self.clone_root}"

    @xray
    def check_github_repo(self, github_url: str) -> str:
        """
        Check if a GitHub repository is accessible (public).
        Returns accessibility status message.
        """
        response = requests.get(github_url, timeout=10)
        
        if response.status_code == 200:
            return "Repository is accessible (public)."
        elif response.status_code == 404:
            return "Repository not found or private! Please link a valid public GitHub repository."
        else:
            return f"Repository returned status {response.status_code}."

    @xray
    def clone_github_repo(self, github_url: str, dest_root: str = str(DEFAULT_CLONE_ROOT)) -> str:
        """
        Clone a public GitHub repository, given a github_url.
        Clones to destination root, by default should be ./repos
        """
        repo_name = github_url.rstrip("/").split("/")[-1] or "repo"
        root = Path(dest_root)
        destination = root / repo_name
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            return f"Repository already exists at {destination}"

        result = subprocess.run(
            ["git", "clone", github_url, str(destination)],
            capture_output=True,
            text=True,
        )

        return f"Cloned to {destination}"

    @xray
    def navigate_and_clone(self, github_url: str, dest_root: str = str(DEFAULT_CLONE_ROOT)) -> str:
        """
        Check if GitHub repo is accessible and clone it if successful.
        One-step function combining check and clone.
        Calling different functions to check accessibility and to clone the repo
        """
        check_result = self.check_github_repo(github_url)
        
        if "accessible (public)" not in check_result:
            return check_result
        
        clone_result = self.clone_github_repo(github_url, dest_root)
        return f"{check_result}\n{clone_result}"


class CodebaseScanner:
    """Scan and analyze codebases using fuzzy matching for better file discovery."""

    # Common file extension types, includes Python, JavaScript, Rust, etc..
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java", ".cpp", ".c", ".h", ".hpp"}

    def __init__(self, codebase_root: Path | str = DEFAULT_CLONE_ROOT):
        self.codebase_root = Path(codebase_root)

    @xray
    def set_codebase_path(self, directory_path: str) -> str:
        """
        Set a custom directory path to scan (can be any local folder).
        Use this when you want to analyze a codebase outside of /repos.
        This sets the default codebase_root for operations that don't specify folder_path or repo_name.
        """
        path = Path(directory_path).expanduser().resolve()
        if not path.exists():
            return f"Directory {directory_path} does not exist."
        if not path.is_dir():
            return f"{directory_path} is not a directory."
        
        self.codebase_root = path
        return f"Codebase path set to {self.codebase_root}"

    @xray
    def list_repositories(self) -> str:
        """
        List all cloned repositories that were previously cloned into '/repos'
        """
        if not self.codebase_root.exists():
            return f"Directory {self.codebase_root} does not exist."
        
        repos = [d.name for d in self.codebase_root.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if not repos:
            return f"No repositories found in {self.codebase_root}. Clone a repo first!"
        
        result = f"Available repositories ({len(repos)}):\n"
        result += "\n".join(f"  - {repo}" for repo in repos)
        return result

    # @xray
    # def get_repo_structure(self, repo_name: str | None = None, folder_path: str | None = None) -> str:
    #     """
    #     Show the directory structure of a repository or folder.
        
    #     Either repo_name (subdirectory of codebase_root) or folder_path (direct path) can be provided.
    #     """
    #     target_dir = self.resolve_target_dir(repo_name=repo_name, folder_path=folder_path)
        
    #     if not target_dir:
    #         identifier = folder_path if folder_path else (repo_name or str(self.codebase_root))
    #         return f"Folder/repository '{identifier}' not found."
        
    #     code_files = self.get_code_files(target_dir)
        
    #     # Group files by directory
    #     dir_structure = {}
    #     for file_path in code_files:
    #         rel_path = file_path.relative_to(target_dir)
    #         parent = str(rel_path.parent) if str(rel_path.parent) != '.' else 'root'
    #         dir_structure.setdefault(parent, []).append(rel_path.name)
        
    #     identifier = folder_path if folder_path else (repo_name if repo_name else str(target_dir))
    #     result = [f"Structure of {identifier}:", "=" * 60, ""]
    #     for directory, files in sorted(dir_structure.items()):
    #         result.append(f"{directory}/ ({len(files)} files)")
    #         for f in sorted(files)[:5]:
    #             result.append(f"   - {f}")
    #         if len(files) > 5:
    #             result.append(f"   ... and {len(files) - 5} more files")
    #         result.append("")
        
    #     return "\n".join(result)

    @xray
    def fuzzy_search_files(self, query: str, repo_name: str | None = None, folder_path: str | None = None, max_results: int = 15) -> str:
        """
        Fuzzy search for files using connectonion's fuzzy_match.
        Returns files ranked by relevance with match highlighting.
        """
        target_dir = self.resolve_target_dir(repo_name=repo_name, folder_path=folder_path)
        
        if not target_dir:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Folder/repository '{identifier}' not found."
        
        code_files = self.get_code_files(target_dir)
        
        if not code_files:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"No code files found in '{identifier}'."
        
        file_paths = [str(f.relative_to(target_dir)) for f in code_files]
        scored_files = self.score_files_fuzzy(query, file_paths)
        
        if not scored_files:
            return f"No files found matching '{query}'."
        
        return self.format_search_results(query, scored_files, max_results)

    @xray
    def recommend_files(self, feature_description: str, repo_name: str | None = None, folder_path: str | None = None) -> str:
        """
        Recommend files relevant to implementing a feature given feature description input
        """
        target_dir = self.resolve_target_dir(repo_name=repo_name, folder_path=folder_path)
        
        if not target_dir:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Folder/repository '{identifier}' not found."
        
        code_files = self.get_code_files(target_dir)
        
        if not code_files:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"No code files found in '{identifier}'."
        
        keywords = feature_description.lower().split()
        scored_files = self.score_files_for_feature(code_files, target_dir, keywords)
        recommended = sorted(scored_files, reverse=True, key=lambda x: x[0])[:5]
        
        return self.format_recommendations(feature_description, recommended)

    @xray
    def explain_file(self, file_path: str, repo_name: str | None = None, folder_path: str | None = None) -> str:
        """
        Explain what a file does by analyzing its structure and content.
        """
        target_dir = self.resolve_target_dir(repo_name=repo_name, folder_path=folder_path)
        
        if not target_dir:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Folder/repository '{identifier}' not found."
            
        full_path = target_dir / file_path
        
        if not full_path.exists():
            identifier = folder_path if folder_path else (repo_name or str(target_dir))
            return f"File {file_path} not found in '{identifier}'."
        
        if not full_path.is_file():
            return f"{file_path} is not a file."
        
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        classes, functions, imports = self.extract_code_elements(lines)
        
        return self.format_file_explanation(file_path, full_path, lines, classes, functions, imports)

    @xray
    def get_file_content(self, file_path: str, repo_name: str | None = None, folder_path: str | None = None, start_line: int = 1, num_lines: int = 50) -> str:
        """
        Get the content of a file, given file path 
        """
        target_dir = self.resolve_target_dir(repo_name=repo_name, folder_path=folder_path)
        
        if not target_dir:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Folder/repository '{identifier}' not found."
            
        full_path = target_dir / file_path
        
        if not full_path.exists():
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"File {file_path} not found in '{identifier}'."
        
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), start_idx + num_lines)
        
        selected_lines = lines[start_idx:end_idx]
        
        result = f"{file_path} (lines {start_line}-{start_idx + len(selected_lines)}):\n"
        result += "=" * 60 + "\n"
        
        for i, line in enumerate(selected_lines, start=start_line):
            result += f"{i:4d} | {line}\n"
        
        if end_idx < len(lines):
            result += f"\n... ({len(lines) - end_idx} more lines)"
        
        return result

    @xray
    def find_function_definition(self, function_name: str, repo_name: str | None = None, folder_path: str | None = None) -> str:
        """
        Find where a function is defined using fuzzy matching.
        """
        target_dir = self.resolve_target_dir(repo_name=repo_name, folder_path=folder_path)
        
        if not target_dir:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Folder/repository '{identifier}' not found."
        
        code_files = self.get_code_files(target_dir)
        matches = []
        
        for file_path in code_files:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            
            for i, line in enumerate(lines, 1):
                # Use fuzzy matching for function names
                if "def " in line or "function " in line:
                    line_lower = line.strip().lower()
                    result = fuzzy_match(function_name.lower(), line_lower)
                    # Check if result is tuple or score
                    score = result[1] if isinstance(result, tuple) and len(result) >= 2 else result
                    if score and score > 0.7:
                        rel_path = file_path.relative_to(target_dir)
                        matches.append((str(rel_path), i, line.strip()))
        
        if not matches:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Function matching '{function_name}' not found in '{identifier}'."
        
        result = f"Found functions matching '{function_name}' ({len(matches)} locations):\n\n"
        for path, line_num, line_content in matches[:10]:
            result += f"  {path}:{line_num}\n"
            result += f"     {line_content}\n\n"
        
        return result

    @xray
    def find_class_definition(self, class_name: str, repo_name: str | None = None, folder_path: str | None = None) -> str:
        """
        Find where a class is defined using fuzzy matching.
        """
        target_dir = self.resolve_target_dir(repo_name=repo_name, folder_path=folder_path)
        
        if not target_dir:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Folder/repository '{identifier}' not found."
        
        code_files = self.get_code_files(target_dir)
        matches = []
        
        for file_path in code_files:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            
            for i, line in enumerate(lines, 1):
                if "class " in line:
                    line_lower = line.strip().lower()
                    result = fuzzy_match(class_name.lower(), line_lower)
                    score = result[1] if isinstance(result, tuple) and len(result) >= 2 else result
                    if score and score > 0.7:
                        rel_path = file_path.relative_to(target_dir)
                        matches.append((str(rel_path), i, line.strip()))
        
        if not matches:
            identifier = folder_path if folder_path else repo_name or "directory"
            return f"Class matching '{class_name}' not found in '{identifier}'."
        
        result = f"Found classes matching '{class_name}' ({len(matches)} locations):\n\n"
        for path, line_num, line_content in matches[:10]:
            result += f"  {path}:{line_num}\n"
            result += f"     {line_content}\n\n"
        
        return result

    # HELPER FUNCTIONS
    def resolve_target_dir(self, repo_name: str | None = None, folder_path: str | None = None) -> Path | None:
        """
        Resolve target directory from either repo_name or folder_path.
        - If folder_path is provided, use it directly (supports absolute/relative paths)
        - If repo_name is provided, assume it's a subdirectory of codebase_root
        - If both are None, use codebase_root directly
        Returns None if path doesn't exist or isn't a directory.
        """
        if folder_path:
            # Make use of local folder path
            path = Path(folder_path).expanduser().resolve()
            if path.exists() and path.is_dir():
                return path
            return None
        
        if repo_name:
            # Make use of repo name under '/repos'
            target_dir = self.codebase_root / repo_name
            if target_dir.exists() and target_dir.is_dir():
                return target_dir
            return None
        
        # Use codebase_root directly
        if self.codebase_root.exists() and self.codebase_root.is_dir():
            return self.codebase_root
        return None

    @xray
    def get_code_files(self, directory: Path) -> List[Path]:
        """Recursively get all code files in directory."""
        if not directory.exists() or not directory.is_dir():
            return []
        return [f for f in directory.rglob("*") if f.is_file() and f.suffix in self.CODE_EXTENSIONS]

    def extract_code_elements(self, lines: List[str]) -> tuple[List[str], List[str], List[str]]:
        """Extract classes, functions, and imports from code."""
        classes, functions, imports = [], [], []
        
        for i, line in enumerate(lines[:100], 1):
            stripped = line.strip()
            
            if stripped.startswith("class "):
                class_name = stripped.split("(")[0].replace("class ", "").strip(":")
                classes.append(f"  - {class_name} (line {i})")
            elif stripped.startswith("def "):
                func_name = stripped.split("(")[0].replace("def ", "").strip()
                if not func_name.startswith("_"):
                    functions.append(f"  - {func_name}() (line {i})")
            elif stripped.startswith(("import ", "from ")):
                imports.append(stripped)
        
        return classes, functions, imports


    def format_file_explanation(self, file_path: str, full_path: Path, lines: List[str], classes: List[str], functions: List[str], imports: List[str]) -> str:
        """Format file explanation with structure and preview."""
        result = [
            f"{file_path}",
            "=" * 60,
            f"Lines: {len(lines)} | Extension: {full_path.suffix}",
            ""
        ]
        
        if imports:
            result.append("Imports:")
            result.extend(f"  - {imp}" for imp in imports[:8])
            result.append("")
        
        if classes:
            result.append("Classes:")
            result.extend(classes[:5])
            result.append("")
        
        if functions:
            result.append("Functions:")
            result.extend(functions[:8])
            result.append("")
        
        preview = "\n".join(lines[:25])
        result.append("Preview (first 25 lines):")
        result.append("-" * 60)
        result.append(preview)
        if len(lines) > 25:
            result.append(f"\n... ({len(lines) - 25} more lines)")
        
        return "\n".join(result)

    def score_files_fuzzy(self, query: str, file_paths: List[str]) -> List[tuple[float, str, str]]:
        """Score files using fuzzy matching and return sorted results with highlighting."""
        scored_files = []
        for path in file_paths:
            result = fuzzy_match(query.lower(), path.lower())
            score = result[1] if isinstance(result, tuple) and len(result) >= 2 else result
            if score > 0:
                highlighted = highlight_match(path, query)
                scored_files.append((score, path, highlighted))
        scored_files.sort(reverse=True, key=lambda x: x[0])
        return scored_files

    def format_search_results(self, query: str, scored_files: List[tuple[float, str, str]], max_results: int) -> str:
        """Format fuzzy search results."""
        result = f"Fuzzy search results for '{query}' ({len(scored_files[:max_results])} matches):\n\n"
        for i, (score, path, highlighted) in enumerate(scored_files[:max_results], 1):
            result += f"  {i}. {highlighted} (score: {score:.2f})\n"
        
        if len(scored_files) > max_results:
            result += f"\n... and {len(scored_files) - max_results} more matches"
        
        return result

    def score_files_for_feature(self, code_files: List[Path], target_dir: Path, keywords: List[str]) -> List[tuple[float, str]]:
        """Score files based on feature keywords using fuzzy matching."""
        scored_files = []
        for file_path in code_files:
            rel_path = str(file_path.relative_to(target_dir))
            total_score = 0
            
            for keyword in keywords:
                path_result = fuzzy_match(keyword, rel_path.lower())
                path_score = path_result[1] if isinstance(path_result, tuple) and len(path_result) >= 2 else path_result
                total_score += path_score * 3
                
                content = file_path.read_text(encoding="utf-8", errors="ignore")[:1000].lower()
                content_result = fuzzy_match(keyword, content)
                content_score = content_result[1] if isinstance(content_result, tuple) and len(content_result) >= 2 else content_result
                total_score += content_score * 2
            
            if total_score > 0:
                scored_files.append((total_score, rel_path))
        
        return scored_files

    def format_recommendations(self, feature_description: str, recommended: List[tuple[float, str]]) -> str:
        """Format file recommendations."""
        result = f"Recommended files for: '{feature_description}'\n\n"
        for i, (score, path) in enumerate(recommended, 1):
            result += f"  {i}. {path} (relevance: {score:.1f})\n"
        result += f"\nUse explain_file() to learn what each file does."
        return result

# Initialize tools and agent
github = GithubAccessLink()
codebase = CodebaseScanner()

agent = Agent(
    "Codebase Assistant",
    tools=[github, codebase],
    system_prompt="prompts/system_prompt.md"
)

def _handle_clone_repo(agent: Agent) -> str | None:
    """Handle cloning a new repository. Returns repo name if successful, None otherwise."""
    print("\nEnter GitHub repository URL:")
    github_url = Input().run()
    if not github_url or github_url.lower() in ['exit', 'quit']:
        return None
    
    response = agent.input(f"Navigate to this repository and clone it: {github_url}")
    print(f"\n{response}")
    
    error_keywords = ["not found", "private", "failed to clone", "can't access", "cannot access", "sorry"]
    if any(keyword in response.lower() for keyword in error_keywords):
        print("\nClone failed. Please try again with a valid public repository.\n")
        return None
    
    return github_url.rstrip("/").split("/")[-1]


def _handle_use_existing_repo() -> str | None:
    """Handle selecting an existing repository. Returns repo name if successful, None otherwise."""
    repos_path = Path("repos")
    if not repos_path.exists():
        print("\nNo repos folder found. Clone a repository first.\n")
        return None
    
    available_repos = [d.name for d in repos_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if not available_repos:
        print("\nNo repositories found in ./repos/")
        print("Please clone a repository first.\n")
        return None
    
    current_repo = pick("Select a repository:", available_repos)
    print(f"\nUsing repository: {current_repo}")
    return current_repo


def _handle_select_folder(codebase: CodebaseScanner) -> str | None:
    """Handle selecting an arbitrary local folder. Returns folder path if successful, None otherwise."""
    print("\nEnter path to local folder (relative to current directory or absolute):")
    print(f"Current directory: {Path.cwd()}")
    folder_input = Input().run()
    if not folder_input or folder_input.lower() in ['exit', 'quit']:
        return None
    
    # Changed path resolution logic to handle relative paths from cwd
    if Path(folder_input).is_absolute():
        folder_path = Path(folder_input).resolve()
    else:
        folder_path = (Path.cwd() / folder_input).resolve()
    
    # Split the error check into two separate conditions
    if not folder_path.exists():
        print(f"\nFolder '{folder_path}' does not exist.\n")
        return None
    
    if not folder_path.is_dir():
        print(f"\n'{folder_path}' is not a directory.\n")
        return None
    
    response = codebase.set_codebase_path(str(folder_path))
    print(f"\n{response}")
    return str(folder_path) 

def _show_chat_intro(current_repo: str | None, current_folder: str | None):
    """Show chat interface introduction with examples."""
    print("\nChat with the assistant about the codebase:")
    if current_repo:
        print(f"Current repo: {current_repo}")
    elif current_folder:
        print(f"Current folder: {current_folder}")
    
    print("Examples:")
    if current_repo:
        print(f"  - 'Show structure of {current_repo}'")
        print(f"  - 'Fuzzy search for auth files in {current_repo}'")
        print(f"  - 'Recommend files for login feature in {current_repo}'")
        print(f"  - 'Explain what main.py does in {current_repo}'")
    elif current_folder:
        print(f"  - 'Show structure' (using folder: {current_folder})")
        print(f"  - 'Fuzzy search for auth files'")
        print(f"  - 'Recommend files for login feature'")
        print(f"  - 'Explain what main.py does'")
    print()


@xray
def _run_chat_loop(agent: Agent, current_repo: str | None):
    """Run interactive chat loop. Exits only after completing recommendations or explanations."""
    while True:
        print("\n> ", end="")
        user_input = Input().run()
        
        if user_input.lower() in ['exit', 'quit', '']:
            print("\nGoodbye!")
            break
        
        # If using a folder path, add folder_path parameter
        if current_folder and "folder_path" not in user_input.lower():
            user_input = f"{user_input} with folder_path={current_folder}"
        # If using a repo from /repos, add repo_name parameter
        elif current_repo and current_repo not in user_input.lower() and "repo_name" not in user_input.lower():
            user_input = f"{user_input} in {current_repo}"
        
        response = agent.input(user_input)
        print(f"\nAssistant: {response}")
        
        # Check if response indicates completion of recommendation or explanation
        response_lower = response.lower()
        # Only exit for specific recommendation/explanation patterns
        if any(phrase in response_lower for phrase in [
            "recommended files for:",
            "found a few files that seem relevant",
            "most relevant ones are",
            "lines:",
            "classes:",
            "functions:",
            "preview (first 25 lines):"
        ]):
            break  # Exit after completing recommendation or explanation


if __name__ == "__main__":
    """Interactive terminal session with TUI components."""
    print("Codebase Assistant")
    print("=" * 60)
    print("Help junior developers navigate and understand codebases.\n")
    
    action = pick("What would you like to do?", [
        "Clone a new repository",
        "Use existing repository",
        "Select arbitrary local folder",
        "Exit"
    ])
    
    current_repo = None
    current_folder = None
    
    if action == "Clone a new repository":
        current_repo = _handle_clone_repo(agent)
    elif action == "Use existing repository":
        current_repo = _handle_use_existing_repo()
    elif action == "Select arbitrary local folder":
        current_folder = _handle_select_folder(codebase)
    elif action == "Exit":
        print("\nGoodbye!")
    
    if current_repo or current_folder:
        _show_chat_intro(current_repo, current_folder)
        _run_chat_loop(agent, current_repo)
