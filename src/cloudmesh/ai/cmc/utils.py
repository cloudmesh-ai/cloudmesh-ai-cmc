# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import pkgutil
import importlib


def register_group_extensions(parent_group, group_package, child_target=None):
    """
    Generic helper to iteratively load all modules in a package
    and call their register() function.

    :param parent_group: The Click group to attach the discovered commands to.
    :param group_package: The Python package/module to scan for extensions.
    :param child_target: Optional. If provided, child modules are registered
                         to this target instead of the parent_group.
    """
    target = child_target or parent_group

    # group_package.__path__ provides the directory of the extension
    for loader, module_name, is_pkg in pkgutil.iter_modules(group_package.__path__):
        # Construct full module path (e.g., cloudmesh.ai.command.sys.info)
        full_name = f"{group_package.__name__}.{module_name}"
        try:
            module = importlib.import_module(full_name)
            if hasattr(module, "register"):
                module.register(target)
        except Exception as e:
            print(f"Error loading extension {full_name}: {e}")
