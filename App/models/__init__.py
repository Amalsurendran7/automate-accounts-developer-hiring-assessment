# models/__init__.py
from sqlmodel import SQLModel

import importlib
import os
import pathlib

# Dynamically import all Python files in models/domain
domain_path = pathlib.Path(__file__).parent / "domain"
for file in os.listdir(domain_path):
    if file.endswith(".py") and file != "__init__.py":
        module_name = f"models.domain.{file[:-3]}"
        importlib.import_module(module_name)
