#!/usr/bin/env python3
"""
crab — Agent shell for entering and leaving repos (MUD rooms).

Enter a repo, pick up its tools, leave when done.
Like crawling from shell to shell.

Usage:
  crab enter <path>         # Enter a repo — loads its tools
  crab leave                # Leave the current repo
  crab list                 # List available repos
  crab whoami               # Show current context
  crab tool <name> [args]   # Run a tool from the current repo
  crab status               # Show all entered repos
"""

import os, sys, json, subprocess, time, threading
from pathlib import Path
from typing import Optional

CRAB_STATE_DIR = Path("/tmp/crab-state")
CRAB_STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = CRAB_STATE_DIR / "state.json"


class CrabShell:
    def __init__(self):
        self.repo_stack = []  # Stack of (name, path, tools) tuples
        self.tools = {}       # Combined tools from current repo + follows
        self.watches = []     # Watched repos
        self.follows = []     # Followed repos
        self.load_state()
    
    def load_state(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                self.repo_stack = data.get("repo_stack", [])
                self.tools = data.get("tools", {})
                self.watches = data.get("watches", [])
                self.follows = data.get("follows", [])
            except: pass
    
    def save_state(self):
        STATE_FILE.write_text(json.dumps({
            "repo_stack": self.repo_stack,
            "tools": self.tools,
            "watches": self.watches,
            "follows": self.follows,
            "timestamp": time.time(),
        }, indent=2))
    
    def _read_manifest(self, path: Path) -> dict:
        """Read MANIFEST.md and extract tool definitions."""
        manifest_file = path / "MANIFEST.md"
        if not manifest_file.exists():
            return {}
        text = manifest_file.read_text()
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    result = yaml.safe_load(parts[1])
                    if isinstance(result, dict):
                        return result
                except:
                    pass
                # Fallback: simple key-value parse
                data = {}
                for line in parts[1].split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, val = line.split(':', 1)
                        data[key.strip()] = val.strip().strip('"').strip("'").strip()
                return data
        return {}
    
    def _detect_tools(self, path: Path, manifest: dict) -> dict:
        """Detect tools from manifest + repo contents."""
        tools = {}
        
        # From manifest
        provides = manifest.get("provides", [])
        if isinstance(provides, list):
            for p in provides:
                if isinstance(p, dict):
                    name = p.get("tool_name", "")
                    if name:
                        endpoint = p.get("endpoint", "")
                        desc = p.get("description", "")
                        tools[name] = {"type": "http" if endpoint else "local", "endpoint": endpoint, "desc": desc}
                elif isinstance(p, str):
                    tools[p] = {"type": "local", "desc": "detected tool"}
        
        # From CRAB/claws directory
        claws_dir = path / "CRAB" / "claws"
        if claws_dir.exists():
            for f in claws_dir.iterdir():
                try:
                    if f.is_file() and f.name != "README.md":
                        tools[f.stem] = {"type": "script", "path": str(f), "desc": f"crab tool: {f.name}"}
                except:
                    pass
        
        return tools
    
    def enter(self, path_str: str):
        """Enter a repo — load its tools and tick config."""
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            print(f"[crab] path not found: {path}")
            return False
        
        manifest = self._read_manifest(path)
        name = manifest.get("name", path.name)
        tools = self._detect_tools(path, manifest)
        
        # Check if already in this repo
        for n, p, _ in self.repo_stack:
            if p == str(path):
                print(f"[crab] already in {name} ({path})")
                return True
        
        self.repo_stack.append((name, str(path), tools))
        self.tools.update(tools)
        self.save_state()
        
        print(f"[crab] entered {name} ({path})")
        print(f"  tools: {len(tools)} available")
        for t in sorted(tools.keys()):
            print(f"    {t}: {tools[t].get('desc', '?')}")
        return True
    
    def leave(self):
        """Leave the current repo."""
        if not self.repo_stack:
            print("[crab] not in any repo")
            return False
        
        name, path, _ = self.repo_stack.pop()
        # Rebuild tools from remaining repos
        self.tools = {}
        for n, p, tools in self.repo_stack:
            self.tools.update(tools)
        self.save_state()
        
        print(f"[crab] left {name}")
        if self.repo_stack:
            current = self.repo_stack[-1]
            print(f"  now in {current[0]} ({len(self.tools)} tools available)")
        return True
    
    def list_available(self, search_dirs: list = None) -> list:
        """Scan directories for repos with MANIFEST.md."""
        search_dirs = search_dirs or [str(Path.home() / ".openclaw/workspace/repos"), "/tmp"]
        found = []
        for search_dir in search_dirs:
            d = Path(search_dir)
            if not d.exists():
                continue
            for item in sorted(d.iterdir()):
                try:
                    if item.is_dir() and (item / "MANIFEST.md").exists():
                        manifest = self._read_manifest(item)
                        name = manifest.get("name", item.name)
                        family = manifest.get("family", "")
                        found.append({"name": name, "family": family, "path": str(item)})
                except PermissionError:
                    continue
        return found
    
    def run_tool(self, tool_name: str, *args):
        """Run a tool from the current repo."""
        if tool_name not in self.tools:
            print(f"[crab] tool not found: {tool_name}")
            print(f"  available: {', '.join(sorted(self.tools.keys()))}")
            return None
        
        tool = self.tools[tool_name]
        
        if tool["type"] == "http":
            # Make HTTP request to the tool endpoint
            endpoint = tool["endpoint"]
            payload = {"args": args} if args else {}
            try:
                import urllib.request
                if "GET" in endpoint.upper():
                    url = f"http://localhost:{endpoint.split(':')[2]}" if ':' in endpoint else endpoint
                    req = urllib.request.Request(url)
                else:
                    req = urllib.request.Request(
                        endpoint,
                        data=json.dumps(payload).encode(),
                        headers={"Content-Type": "application/json"},
                    )
                resp = urllib.request.urlopen(req, timeout=10)
                return json.loads(resp.read())
            except Exception as e:
                return {"error": str(e)}
        
        elif tool["type"] == "script":
            # Run a local script
            try:
                result = subprocess.run(
                    [tool["path"]] + list(args),
                    capture_output=True, text=True, timeout=30,
                )
                return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
            except subprocess.TimeoutExpired:
                return {"error": "timeout"}
            except Exception as e:
                return {"error": str(e)}
        
        elif tool["type"] == "local":
            # Remove -- try to find and run it
            # Check src/, scripts/, or root
            for repo_name, repo_path, _ in self.repo_stack:
                for candidate in ["src", "scripts", "."]:
                    script = Path(repo_path) / candidate / tool_name
                    if script.exists():
                        result = subprocess.run(
                            [str(script)] + list(args),
                            capture_output=True, text=True, timeout=30,
                        )
                        return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
            return {"error": f"no executable found for {tool_name}"}
        
        return {"error": f"unknown tool type: {tool['type']}"}
    
    def status(self) -> dict:
        return {
            "current_repo": self.repo_stack[-1] if self.repo_stack else None,
            "in_repos": len(self.repo_stack),
            "repo_stack": [(n, p) for n, p, _ in self.repo_stack],
            "tools_available": len(self.tools),
            "tools": list(self.tools.keys()),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="crab — enter and leave repos")
    parser.add_argument("command", nargs="?", default="status")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--version", action="version", version="crab 0.1.0")
    args = parser.parse_args()
    
    shell = CrabShell()
    
    if args.command == "enter":
        if args.args:
            shell.enter(args.args[0])
        else:
            print("[crab] enter: need path to repo")
    
    elif args.command == "leave":
        shell.leave()
    
    elif args.command == "list":
        found = shell.list_available()
        print(f"Available repos ({len(found)}):")
        for repo in found:
            fam = f" ({repo['family']})" if repo['family'] else ""
            print(f"  {repo['name']:30s}{fam:20s} {repo['path']}")
    
    elif args.command == "whoami":
        status = shell.status()
        if status["current_repo"]:
            name, path, _ = status["current_repo"]
            print(f"  Current: {name} ({path})")
            print(f"  Stack depth: {status['in_repos']}")
            print(f"  Tools ({status['tools_available']}):")
            for t in sorted(status["tools"]):
                print(f"    {t}")
        else:
            print("  Not in any repo")
            print("  Use: crab enter <path>")
    
    elif args.command == "tool":
        if args.args:
            result = shell.run_tool(args.args[0], *args.args[1:])
            if result:
                print(json.dumps(result, indent=2))
        else:
            print("[crab] tool: need tool name")
    
    elif args.command == "status":
        status = shell.status()
        print(f"Entered repos: {status['in_repos']}")
        for name, path in status["repo_stack"]:
            print(f"  {name:30s} {path}")
        print(f"Tools loaded: {status['tools_available']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
