import json
import os
from typing import Dict, List, Optional

class Storage:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.projects_file = os.path.join(data_dir, "projects.json")
        self.config_file = os.path.join(data_dir, "config.json")
        os.makedirs(data_dir, exist_ok=True)
        self._init_files()

    def _init_files(self):
        if not os.path.exists(self.projects_file):
            self._save_json(self.projects_file, {})
        if not os.path.exists(self.config_file):
            self._save_json(self.config_file, {})

    def _load_json(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save_json(self, file_path: str, data: Dict):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_projects(self) -> List[str]:
        projects = self._load_json(self.projects_file)
        return list(projects.keys())

    def get_project(self, project_name: str) -> Optional[Dict]:
        projects = self._load_json(self.projects_file)
        return projects.get(project_name)

    def save_project(self, project_name: str, variable_name: str, separator: str, instance_name: str = "", variable_description: str = ""):
        projects = self._load_json(self.projects_file)
        if project_name not in projects:
            projects[project_name] = {
                "variable_name": variable_name,
                "variable_description": variable_description,
                "separator": separator,
                "instance_name": instance_name,
                "accounts": {}
            }
        else:
            projects[project_name]["variable_name"] = variable_name
            projects[project_name]["variable_description"] = variable_description
            projects[project_name]["separator"] = separator
            projects[project_name]["instance_name"] = instance_name
        self._save_json(self.projects_file, projects)

    def add_or_update_account(self, project_name: str, remark: str, value: str):
        projects = self._load_json(self.projects_file)
        if project_name not in projects:
            projects[project_name] = {
                "variable_name": "",
                "separator": "#",
                "accounts": {}
            }
        projects[project_name]["accounts"][remark] = value
        self._save_json(self.projects_file, projects)

    def delete_account(self, project_name: str, remark: str):
        projects = self._load_json(self.projects_file)
        if project_name in projects and remark in projects[project_name]["accounts"]:
            del projects[project_name]["accounts"][remark]
            self._save_json(self.projects_file, projects)
    
    def delete_project(self, project_name: str):
        projects = self._load_json(self.projects_file)
        projects.pop(project_name, None)
        self._save_json(self.projects_file, projects)

    def get_projects_grouped(self):
        """返回 { instance_name: [project_name, ...] }"""
        projects = self._load_json(self.projects_file)
        grouped = {}
        for pname, pdata in projects.items():
            inst = pdata.get("instance_name", "")
            grouped.setdefault(inst, []).append(pname)
        return grouped        

    def get_config(self) -> Dict:
        return self._load_json(self.config_file)

    def save_config(self, config: Dict):
        self._save_json(self.config_file, config)