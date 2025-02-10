import ast
import inspect
import os
import sys
import logging


def _get_local_files(func):
    file_path = inspect.getfile(func)

    ROOT_DIR = os.path.abspath(os.curdir)
    relative_file_path = os.path.relpath(file_path, ROOT_DIR)

    imports = get_imports(file_path)
    local_files = resolve_import_paths(imports, file_path) + [relative_file_path]
    
    for path in local_files:
        logging.info(f"Found local file: {path} ")
    return local_files
    

def get_imports(file_path):
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read(), filename=file_path)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if module:
                imports.append(module)
    return imports


def resolve_import_paths(imports, importing_file):
    all_modules = list(sys.modules.keys())
    file_candidates = [] 
    for module in all_modules:
        if any(module.startswith(imported_name) for imported_name in imports):
            file_candidates.append(module)

    file_candidates.extend(imports)
    ROOT_DIR = os.path.abspath(os.curdir)

    local_files = []
    importing_dir = os.path.dirname(importing_file)

    for module in set(file_candidates):
        if module.startswith('.'):
            level = len(module) - len(module.lstrip('.'))
            parent_dir = importing_dir
            for _ in range(level):
                parent_dir = os.path.dirname(parent_dir)
            rel_path = module.lstrip('.').replace('.', os.sep) + '.py'
            full_path = os.path.join(parent_dir, rel_path)
            if os.path.exists(full_path):
                local_files.append(full_path)
        else:  
            # Handle absolute imports
            # if a local file exists, add its paths
            module_path = module.replace('.', os.sep) + '.py'
            full_path = os.path.join(ROOT_DIR, module_path)
            if os.path.exists(full_path):
                local_files.append(module_path)
    return local_files