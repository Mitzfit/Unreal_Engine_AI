"""
Advanced Save & Export System
Supports multiple formats, version control, and team collaboration
"""

import os
import json
import zipfile
import shutil
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
import asyncio

@dataclass
class ProjectMetadata:
    """Metadata for saved projects"""
    project_id: str
    name: str
    created_at: str
    updated_at: str
    version: str
    author: str
    team_id: Optional[str] = None
    description: str = ""
    tags: List[str] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class AssetExport:
    """Export data for an asset"""
    asset_id: str
    asset_type: str
    name: str
    files: List[str]
    metadata: Dict[str, Any]
    dependencies: List[str] = None

class SaveExportManager:
    """
    Comprehensive save/export system with team collaboration
    """
    
    def __init__(self, base_path: str = "exports"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "projects").mkdir(exist_ok=True)
        (self.base_path / "assets").mkdir(exist_ok=True)
        (self.base_path / "code").mkdir(exist_ok=True)
        (self.base_path / "team_shared").mkdir(exist_ok=True)
        (self.base_path / "backups").mkdir(exist_ok=True)
        
        self.current_project = None
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5 minutes
        
    # ===== PROJECT MANAGEMENT =====
    
    def create_project(
        self,
        name: str,
        author: str,
        team_id: Optional[str] = None,
        description: str = ""
    ) -> ProjectMetadata:
        """Create a new project"""
        
        project_id = self._generate_id(name)
        timestamp = datetime.now().isoformat()
        
        metadata = ProjectMetadata(
            project_id=project_id,
            name=name,
            created_at=timestamp,
            updated_at=timestamp,
            version="1.0.0",
            author=author,
            team_id=team_id,
            description=description,
            tags=[]
        )
        
        # Create project directory
        project_dir = self.base_path / "projects" / project_id
        project_dir.mkdir(exist_ok=True)
        
        # Save metadata
        self._save_metadata(project_dir, metadata)
        
        self.current_project = metadata
        return metadata
    
    def save_project(
        self,
        assets: List[Dict[str, Any]],
        code_files: List[str],
        auto_backup: bool = True
    ) -> str:
        """Save current project state"""
        
        if not self.current_project:
            raise ValueError("No active project")
        
        project_dir = self.base_path / "projects" / self.current_project.project_id
        
        # Create timestamped save
        timestamp = int(time.time())
        save_dir = project_dir / f"save_{timestamp}"
        save_dir.mkdir(exist_ok=True)
        
        # Save assets
        assets_data = []
        for asset in assets:
            asset_export = self._export_asset(asset, save_dir)
            assets_data.append(asset_export.to_dict() if hasattr(asset_export, 'to_dict') else asset_export)
        
        # Save code files
        code_dir = save_dir / "code"
        code_dir.mkdir(exist_ok=True)
        for code_file in code_files:
            if os.path.exists(code_file):
                shutil.copy(code_file, code_dir / os.path.basename(code_file))
        
        # Save project state
        project_state = {
            "metadata": self.current_project.to_dict(),
            "assets": assets_data,
            "code_files": [os.path.basename(f) for f in code_files],
            "saved_at": datetime.now().isoformat()
        }
        
        with open(save_dir / "project_state.json", 'w') as f:
            json.dump(project_state, f, indent=2)
        
        # Update project metadata
        self.current_project.updated_at = datetime.now().isoformat()
        self._save_metadata(project_dir, self.current_project)
        
        # Create backup if requested
        if auto_backup:
            self._create_backup(save_dir)
        
        return str(save_dir)
    
    def load_project(self, project_id: str) -> Dict[str, Any]:
        """Load a project"""
        
        project_dir = self.base_path / "projects" / project_id
        
        if not project_dir.exists():
            raise FileNotFoundError(f"Project {project_id} not found")
        
        # Load metadata
        metadata = self._load_metadata(project_dir)
        self.current_project = metadata
        
        # Find latest save
        saves = sorted(project_dir.glob("save_*"), key=lambda x: x.name, reverse=True)
        
        if not saves:
            return {"metadata": metadata.to_dict(), "assets": [], "code_files": []}
        
        latest_save = saves[0]
        
        with open(latest_save / "project_state.json", 'r') as f:
            project_state = json.load(f)
        
        return project_state
    
    # ===== EXPORT FORMATS =====
    
    def export_unreal_plugin(
        self,
        output_path: str,
        plugin_name: str,
        code_files: List[str],
        assets: List[Dict[str, Any]]
    ) -> str:
        """Export as Unreal Engine plugin"""
        
        plugin_dir = Path(output_path) / plugin_name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create plugin structure
        (plugin_dir / "Source" / plugin_name / "Public").mkdir(parents=True, exist_ok=True)
        (plugin_dir / "Source" / plugin_name / "Private").mkdir(parents=True, exist_ok=True)
        (plugin_dir / "Content").mkdir(parents=True, exist_ok=True)
        (plugin_dir / "Resources").mkdir(parents=True, exist_ok=True)
        
        # Create .uplugin file
        uplugin = {
            "FileVersion": 3,
            "Version": 1,
            "VersionName": "1.0.0",
            "FriendlyName": plugin_name,
            "Description": "AI Generated Plugin",
            "Category": "AI Generated",
            "CreatedBy": self.current_project.author if self.current_project else "AI Architect",
            "CreatedByURL": "",
            "DocsURL": "",
            "MarketplaceURL": "",
            "SupportURL": "",
            "CanContainContent": True,
            "IsBetaVersion": False,
            "IsExperimentalVersion": False,
            "Installed": False,
            "Modules": [
                {
                    "Name": plugin_name,
                    "Type": "Runtime",
                    "LoadingPhase": "Default"
                }
            ]
        }
        
        with open(plugin_dir / f"{plugin_name}.uplugin", 'w') as f:
            json.dump(uplugin, f, indent=2)
        
        # Copy code files
        for code_file in code_files:
            if os.path.exists(code_file):
                filename = os.path.basename(code_file)
                target_dir = plugin_dir / "Source" / plugin_name / ("Public" if filename.endswith('.h') else "Private")
                shutil.copy(code_file, target_dir / filename)
        
        # Generate Build.cs
        build_cs = self._generate_build_cs(plugin_name)
        with open(plugin_dir / "Source" / plugin_name / f"{plugin_name}.Build.cs", 'w') as f:
            f.write(build_cs)
        
        # Copy assets
        for asset in assets:
            # Asset copying logic here
            pass
        
        # Create README
        readme = f"""# {plugin_name}

AI Generated Unreal Engine Plugin

## Installation

1. Copy this folder to your project's Plugins directory
2. Regenerate project files
3. Build your project
4. Enable the plugin in Unreal Editor

## Usage

[Add usage instructions here]

## Generated with AI Architect
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(plugin_dir / "README.md", 'w') as f:
            f.write(readme)
        
        # Create zip archive
        zip_path = f"{output_path}/{plugin_name}.zip"
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', plugin_dir)
        
        return zip_path
    
    def export_standalone_package(
        self,
        output_path: str,
        package_name: str,
        include_source: bool = True,
        include_documentation: bool = True
    ) -> str:
        """Export as standalone package"""
        
        package_dir = Path(output_path) / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.current_project:
            raise ValueError("No active project")
        
        # Load latest project state
        project_state = self.load_project(self.current_project.project_id)
        
        # Create package structure
        (package_dir / "Source").mkdir(exist_ok=True)
        (package_dir / "Assets").mkdir(exist_ok=True)
        (package_dir / "Documentation").mkdir(exist_ok=True)
        
        # Copy all files
        project_dir = self.base_path / "projects" / self.current_project.project_id
        latest_save = sorted(project_dir.glob("save_*"), key=lambda x: x.name, reverse=True)[0]
        
        if include_source:
            shutil.copytree(latest_save / "code", package_dir / "Source", dirs_exist_ok=True)
        
        # Generate documentation
        if include_documentation:
            self._generate_documentation(package_dir / "Documentation", project_state)
        
        # Create package info
        package_info = {
            "name": package_name,
            "version": self.current_project.version,
            "author": self.current_project.author,
            "created": self.current_project.created_at,
            "exported": datetime.now().isoformat(),
            "assets": len(project_state.get("assets", [])),
            "code_files": len(project_state.get("code_files", []))
        }
        
        with open(package_dir / "package.json", 'w') as f:
            json.dump(package_info, f, indent=2)
        
        # Create archive
        archive_path = f"{output_path}/{package_name}.tar.gz"
        shutil.make_archive(archive_path.replace('.tar.gz', ''), 'gztar', package_dir)
        
        return archive_path
    
    def export_git_repository(
        self,
        repo_path: str,
        commit_message: str = "AI Generated Export"
    ) -> str:
        """Export to Git repository"""
        
        import subprocess
        
        repo_dir = Path(repo_path)
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize git if not exists
        if not (repo_dir / ".git").exists():
            subprocess.run(["git", "init"], cwd=repo_dir)
            subprocess.run(["git", "config", "user.name", "AI Architect"], cwd=repo_dir)
            subprocess.run(["git", "config", "user.email", "ai@architect.dev"], cwd=repo_dir)
        
        # Copy project files
        if self.current_project:
            project_state = self.load_project(self.current_project.project_id)
            
            # Copy code
            code_dir = repo_dir / "Source"
            code_dir.mkdir(exist_ok=True)
            
            project_dir = self.base_path / "projects" / self.current_project.project_id
            latest_save = sorted(project_dir.glob("save_*"), key=lambda x: x.name, reverse=True)[0]
            
            if (latest_save / "code").exists():
                shutil.copytree(latest_save / "code", code_dir, dirs_exist_ok=True)
        
        # Create .gitignore
        gitignore = """# Build files
*.obj
*.o
*.exe
*.dll
*.so
*.dylib

# IDE
.vs/
.vscode/
.idea/

# Unreal
Binaries/
Intermediate/
Saved/
DerivedDataCache/
"""
        with open(repo_dir / ".gitignore", 'w') as f:
            f.write(gitignore)
        
        # Git commit
        subprocess.run(["git", "add", "."], cwd=repo_dir)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_dir)
        
        return str(repo_dir)
    
    # ===== TEAM COLLABORATION =====
    
    async def share_with_team(
        self,
        team_id: str,
        project_id: str,
        permissions: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """Share project with team"""
        
        if permissions is None:
            permissions = {
                "view": True,
                "edit": False,
                "delete": False,
                "share": False
            }
        
        # Copy to team shared directory
        project_dir = self.base_path / "projects" / project_id
        team_dir = self.base_path / "team_shared" / team_id
        team_dir.mkdir(parents=True, exist_ok=True)
        
        shared_project_dir = team_dir / project_id
        shutil.copytree(project_dir, shared_project_dir, dirs_exist_ok=True)
        
        # Create team permissions file
        team_permissions = {
            "team_id": team_id,
            "project_id": project_id,
            "shared_at": datetime.now().isoformat(),
            "shared_by": self.current_project.author if self.current_project else "Unknown",
            "permissions": permissions
        }
        
        with open(shared_project_dir / "team_permissions.json", 'w') as f:
            json.dump(team_permissions, f, indent=2)
        
        return team_permissions
    
    async def sync_with_team(
        self,
        team_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Sync project with team version"""
        
        team_dir = self.base_path / "team_shared" / team_id / project_id
        local_dir = self.base_path / "projects" / project_id
        
        if not team_dir.exists():
            return {"error": "Team project not found"}
        
        # Compare versions
        team_metadata = self._load_metadata(team_dir)
        local_metadata = self._load_metadata(local_dir)
        
        team_updated = datetime.fromisoformat(team_metadata.updated_at)
        local_updated = datetime.fromisoformat(local_metadata.updated_at)
        
        if team_updated > local_updated:
            # Pull from team
            shutil.copytree(team_dir, local_dir, dirs_exist_ok=True)
            return {"action": "pulled", "from": "team", "updated": team_metadata.updated_at}
        elif local_updated > team_updated:
            # Push to team
            shutil.copytree(local_dir, team_dir, dirs_exist_ok=True)
            return {"action": "pushed", "to": "team", "updated": local_metadata.updated_at}
        else:
            return {"action": "none", "message": "Already in sync"}
    
    def get_team_projects(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all projects shared with team"""
        
        team_dir = self.base_path / "team_shared" / team_id
        
        if not team_dir.exists():
            return []
        
        projects = []
        for project_dir in team_dir.iterdir():
            if project_dir.is_dir():
                metadata = self._load_metadata(project_dir)
                
                # Load permissions
                permissions_file = project_dir / "team_permissions.json"
                permissions = {}
                if permissions_file.exists():
                    with open(permissions_file, 'r') as f:
                        perms_data = json.load(f)
                        permissions = perms_data.get("permissions", {})
                
                projects.append({
                    "metadata": metadata.to_dict(),
                    "permissions": permissions
                })
        
        return projects
    
    # ===== AUTO-SAVE =====
    
    async def start_auto_save(self, callback):
        """Start auto-save loop"""
        
        while self.auto_save_enabled:
            await asyncio.sleep(self.auto_save_interval)
            
            if self.current_project:
                try:
                    # Get current state from callback
                    state = callback()
                    if state:
                        self.save_project(
                            assets=state.get("assets", []),
                            code_files=state.get("code_files", []),
                            auto_backup=False
                        )
                        print(f"[AUTO-SAVE] Project saved at {datetime.now().strftime('%H:%M:%S')}")
                except Exception as e:
                    print(f"[AUTO-SAVE] Error: {e}")
    
    # ===== HELPER METHODS =====
    
    def _generate_id(self, name: str) -> str:
        """Generate unique ID"""
        timestamp = str(int(time.time()))
        return hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:12]
    
    def _save_metadata(self, directory: Path, metadata: ProjectMetadata):
        """Save metadata to directory"""
        with open(directory / "metadata.json", 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    
    def _load_metadata(self, directory: Path) -> ProjectMetadata:
        """Load metadata from directory"""
        with open(directory / "metadata.json", 'r') as f:
            data = json.load(f)
            return ProjectMetadata(**data)
    
    def _export_asset(self, asset: Dict[str, Any], save_dir: Path) -> Dict[str, Any]:
        """Export single asset"""
        
        asset_dir = save_dir / "assets" / asset.get("name", "asset")
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        # Save asset data
        with open(asset_dir / "asset.json", 'w') as f:
            json.dump(asset, f, indent=2)
        
        return {
            "asset_id": asset.get("name", "unknown"),
            "asset_type": asset.get("type", "unknown"),
            "name": asset.get("name", "asset"),
            "files": [str(asset_dir / "asset.json")],
            "metadata": asset
        }
    
    def _create_backup(self, source_dir: Path):
        """Create backup of save"""
        
        backup_name = f"backup_{int(time.time())}"
        backup_dir = self.base_path / "backups" / backup_name
        
        shutil.copytree(source_dir, backup_dir)
        
        # Keep only last 10 backups
        backups = sorted(self.base_path.glob("backups/backup_*"), key=lambda x: x.name)
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                shutil.rmtree(old_backup)
    
    def _generate_build_cs(self, module_name: str) -> str:
        """Generate Unreal Build.cs file"""
        
        return f'''using UnrealBuildTool;

public class {module_name} : ModuleRules
{{
    public {module_name}(ReadOnlyTargetRules Target) : base(Target)
    {{
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] 
        {{ 
            "Core", 
            "CoreUObject", 
            "Engine", 
            "InputCore" 
        }});

        PrivateDependencyModuleNames.AddRange(new string[] {{ }});
    }}
}}
'''
    
    def _generate_documentation(self, doc_dir: Path, project_state: Dict[str, Any]):
        """Generate project documentation"""
        
        # Generate README
        readme = f"""# {project_state['metadata']['name']}

## Project Information
- **Author**: {project_state['metadata']['author']}
- **Created**: {project_state['metadata']['created_at']}
- **Version**: {project_state['metadata']['version']}

## Description
{project_state['metadata'].get('description', 'No description provided')}

## Assets
Total Assets: {len(project_state.get('assets', []))}

## Code Files
Total Files: {len(project_state.get('code_files', []))}

## Export Information
- **Exported**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Generated by**: AI Architect Ultimate Edition

## Usage
[Add usage instructions here]

## License
[Add license information here]
"""
        
        with open(doc_dir / "README.md", 'w') as f:
            f.write(readme)
        
        # Generate API documentation
        api_doc = """# API Documentation

[Add API documentation here]
"""
        with open(doc_dir / "API.md", 'w') as f:
            f.write(api_doc)
