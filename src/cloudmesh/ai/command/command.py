import click
import sys
import inspect
from cloudmesh.ai.common.io import console
from cloudmesh.ai.command.man import generate_manual, get_formatter
import os
from pathlib import Path
import re

# ==============================================================================
# COMMAND DEFINITIONS
# All functions starting with 'cmd_' will be automatically registered
# ==============================================================================


@click.command(name="load")
@click.argument("directory", type=click.Path(exists=True))
@click.option(
    "--name", "-n", help="Custom name for the extension"
)
def cmd_load(directory, name):
    """Register and load a new command."""
    from cloudmesh.ai.cmc.main import registry

    registry.register(name, directory)
    # Derive the name if not provided for the output message
    display_name = name or os.path.basename(os.path.abspath(directory))
    console.ok(f"Loaded and activated: {display_name}")


@click.command(name="activate")
@click.argument("name")
def cmd_activate(name):
    """Activate a registered command."""
    from cloudmesh.ai.cmc.main import registry

    if registry.set_status(name, True):
        console.ok(f"Activated: {name}")
    else:
        console.error(f"{name} not found in registry.")


@click.command(name="deactivate")
@click.argument("name")
def cmd_deactivate(name):
    """Deactivate a registered command."""
    from cloudmesh.ai.cmc.main import registry

    if registry.set_status(name, False):
        console.ok(f"Deactivated: {name}")
    else:
        console.error(f"{name} not found in registry.")


@click.command(name="list")
def cmd_list():
    """List all available AI extensions (Core, Pip, and Registered)."""
    from cloudmesh.ai.cmc.main import registry, cli
    
    # 1. Get Registered extensions (local paths)
    registered = registry.list_all_details()
    
    # 2. Identify all other loaded commands from the CLI root
    all_loaded = []
    for name, cmd in cli.commands.items():
        # Skip the 'command' group itself
        if name == "command":
            continue
            
        # Determine source
        source = "Core"
        path = "Built-in"
        version = "Core"
        
        # Check if it's a LazyCommand (likely Pip)
        if hasattr(cmd, 'module_name') and hasattr(cmd, 'entry_point_name'):
            source = "Pip"
            path = cmd.module_name
            version = "Installed"
        
        # Check if it's in the registry (Local)
        if name in registry.extensions:
            source = "Registered"
            reg_data = registry.extensions[name]
            path = reg_data.get("path", "Unknown")
            version = reg_data.get("version", "0.0.0")
            status = "[green]active[/green]" if reg_data.get("active") else "[red]inactive[/red]"
        else:
            status = "[green]active[/green]"

        all_loaded.append((name, version, status, source, path))

    if not all_loaded:
        console.warning("No AI extensions found.")
        return

    # Sort by source (Core -> Pip -> Registered)
    all_loaded.sort(key=lambda x: (x[3] != "Core", x[3] != "Pip", x[0]))
    
    console.table(
        ["COMMAND", "VERSION", "STATUS", "SOURCE", "PATH"], 
        all_loaded, 
        title="CME AI Extension Registry"
    )


@click.command(name="unload")
@click.argument("name")
def cmd_unload(name):
    """Remove a command from the registry."""
    from cloudmesh.ai.cmc.main import registry

    registry.unregister(name)
    console.ok(f"Unloaded: {name}")


@click.command(name="upload")
@click.argument("path", type=click.Path(exists=True))
@click.option("--org", default="cloudmesh-ai", help="GitHub organization to upload to. Default: cloudmesh-ai")
def cmd_upload(path, org):
    """Upload the command project to GitHub."""
    import subprocess
    
    target_path = Path(path).expanduser().resolve()
    repo_name = target_path.name
    full_repo_path = f"{org}/{repo_name}"
    
    console.info(f"Preparing to upload {repo_name} to {full_repo_path}...")

    # 1. Ensure .gitignore exists to avoid uploading junk
    gitignore_path = target_path / ".gitignore"
    gitignore_content = (
        "__pycache__/\n"
        "*.py[cod]\n"
        "*.so\n"
        ".egg-info/\n"
        "build/\n"
        "dist/\n"
        ".DS_Store\n"
        ".venv/\n"
        "venv/\n"
    )
    if not gitignore_path.exists():
        gitignore_path.write_text(gitignore_content)
        console.info("Created .gitignore to exclude artifacts.")

    def run_cmd(cmd, cwd=None):
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result

    # Ensure git is initialized locally before any GH or Git operations
    if not (target_path / ".git").exists():
        console.info("Initializing local git repository...")
        run_cmd("git init", cwd=target_path)

    # Ensure there is at least one commit so that 'gh repo create --push' works
    run_cmd("git add .", cwd=target_path)
    commit_res = run_cmd('git commit -m "Initial commit from CMC upload"', cwd=target_path)
    if "nothing to commit" not in commit_res.stdout and "nothing to commit" not in commit_res.stderr:
        console.info("Created initial commit for upload.")

    # 2. Check if repo exists on GitHub
    check_repo = run_cmd(f"gh repo view {full_repo_path}")
    
    if check_repo.returncode != 0:
        # Repo doesn't exist, create it
        console.info(f"Repository {full_repo_path} not found. Creating it...")
        # Use absolute path for --source to avoid dependency on current shell directory
        create_repo = run_cmd(f"gh repo create {full_repo_path} --public --source='{target_path}' --remote=origin --push", cwd=target_path)
        if create_repo.returncode == 0:
            console.ok(f"Successfully created and uploaded {full_repo_path}")
        else:
            console.error(f"Failed to create repository: {create_repo.stderr}")
    else:
        # Repo exists, update it
        console.info(f"Repository {full_repo_path} exists. Updating files...")
        
        # Ensure remote is set
        remote_check = run_cmd("git remote", cwd=target_path)
        if full_repo_path.split('/')[-1] not in remote_check.stdout:
            run_cmd(f"git remote add origin https://github.com/{full_repo_path}.git", cwd=target_path)
        
        # Stage and push
        run_cmd("git add .", cwd=target_path)
        commit_res = run_cmd('git commit -m "Update from CMC upload"', cwd=target_path)
        
        if "nothing to commit" in commit_res.stdout or "nothing to commit" in commit_res.stderr:
            console.info("No new changes to upload.")
        else:
            push_res = run_cmd("git push origin main", cwd=target_path)
            if push_res.returncode != 0:
                # Try master if main fails
                push_res = run_cmd("git push origin master", cwd=target_path)
                
            if push_res.returncode == 0:
                console.ok(f"Successfully updated {full_repo_path}")
            else:
                console.error(f"Failed to push changes: {push_res.stderr}")


@click.command(name="create")
@click.argument("name")
@click.option(
    "--groups", "-g", multiple=True, help="Additional sub-commands to create."
)
@click.option("--path", "-p", default=".", help="Path to create the command in.")
def cmd_create(name, groups, path):
    """
    Create or expand a CMC command using the example template.
    """
    root_name = name
    all_subs = list(groups)

    if not all_subs:
        all_subs = [root_name]

    # Template source
    example_dir = Path("/Users/grey/work/cloudmesh-ai-example")
    base_dir = Path(path).expanduser().resolve()
    target_dir = base_dir / f"cloudmesh-ai-{root_name}"
    plugin_file = target_dir / "src" / "cloudmesh" / "ai" / "command" / f"{root_name}.py"

    if target_dir.exists():
        console.warning(f"The command '{root_name}' in the directory '{target_dir.name}' already exists.")
        if click.confirm("Do you want to erase it and create a new one?", default=False):
            import shutil
            shutil.rmtree(target_dir)
        elif plugin_file.exists():
            # Directory exists and is a valid command, proceed to expand
            content = plugin_file.read_text()
            existing_cmds = re.findall(rf'@{root_name}_group\.command\(name="([^"]+)"\)', content)

            new_additions_code = []
            added_names = []

            for sub in all_subs:
                if sub in existing_cmds:
                    console.warning(f"'{sub}' already exists. Skipping.")
                else:
                    code = f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} command added via CMC."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
                    new_additions_code.append(code)
                    added_names.append(sub)

            if not added_names:
                return

            if "def register(cli):" in content:
                parts = content.split("def register(cli):")
                new_content = parts[0] + "".join(new_additions_code) + "def register(cli):" + parts[1]
                plugin_file.write_text(new_content)
                console.ok(f"Updated extension {root_name} with {added_names}")
            return

    try:
        import shutil
        # Copy the example template, ignoring .git directory
        shutil.copytree(example_dir, target_dir, ignore=shutil.ignore_patterns('.git'))

        # Replace placeholders in all files and rename files
        # We collect paths first to avoid issues with modifying the directory tree while iterating
        for file_path in list(target_dir.rglob("*")):
            if file_path.is_file():
                # Replace content
                content = file_path.read_text(errors="ignore")
                new_content = content.replace("{{name}}", root_name)
                file_path.write_text(new_content, encoding="utf-8")
                
                # Rename file if it contains placeholder or is the example plugin
                if "{{name}}" in file_path.name:
                    new_name = file_path.name.replace("{{name}}", root_name)
                    file_path.rename(file_path.with_name(new_name))
                elif file_path.name == "example.py":
                    new_name = f"{root_name}.py"
                    file_path.rename(file_path.with_name(new_name))

        # Handle sub-commands (groups) in the plugin file
        plugin_content = plugin_file.read_text()
        
        if all_subs != [root_name]:
            # Remove the default 'hello' command if we have specific groups
            plugin_content = re.sub(r'@\w+_group\.command\(name="hello"\).*?def hello_cmd\(\):.*?console\.ok\(.*?\)', '', plugin_content, flags=re.DOTALL)
            
            commands_code_list = [
                f'\n\n@{root_name}_group.command(name="{sub}")\ndef {sub}_cmd():\n    """{sub} created by CMC."""\n    console.print("[bold green]Hello from {root_name} {sub}![/bold green]")\n'
                for sub in all_subs
            ]
            
            if "def register(cli):" in plugin_content:
                parts = plugin_content.split("def register(cli):")
                plugin_content = parts[0] + "".join(commands_code_list) + "def register(cli):" + parts[1]
            
            plugin_file.write_text(plugin_content)

        # Collect created files for the banner
        created_files = []
        try:
            rel_target = target_dir.relative_to(Path.cwd())
            created_files.append(f"./{rel_target}/")
        except ValueError:
            created_files.append(f"{target_dir}/")

        for file in target_dir.rglob("*"):
            if file.is_file():
                created_files.append(f"    - {file.relative_to(target_dir)}")

        console.banner("Extension Created", "\n".join(created_files))
        console.ok(f"Created new command at {target_dir}")
    except Exception as e:
        console.error(f"Failed to create extension: {e}")


@click.command(name="man")
@click.option("--all", is_flag=True, help="Generate a manual for all commands.")
@click.option(
    "--format",
    type=click.Choice(["md", "rst", "txt", "text", "qmd", "groff", "html"]),
    default="text",
)
@click.argument("command_name", required=False)
@click.pass_context
def cmd_man(ctx, all, format, command_name):
    """Display or generate the manual for CME commands."""
    
    # Navigation: Find the root 'cmc' group
    # ctx.parent is 'command' group context
    # ctx.parent.parent is the root 'cmc' context
    root_cli = None
    if ctx.parent and ctx.parent.parent:
        root_cli = ctx.parent.parent.command # This is the root Group object
    elif ctx.parent:
        root_cli = ctx.parent.command
    else:
        root_cli = ctx.command

    if all:
        # Generate manual for everything under root
        content = generate_manual(ctx, root_cli, format)
        click.echo(content)
        ctx.exit()

    if command_name:
        # Use root_cli (Group) to find the command
        cmd = root_cli.get_command(ctx, command_name)
        if cmd:
            formatter = get_formatter(format)
            console.print(formatter.format_single(ctx, command_name, cmd))
            ctx.exit()
        else:
            console.error(f"Command '{command_name}' not found.")
            sys.exit(1)

    # If nothing specific requested, show the help for 'man'
    console.print(ctx.get_help())


# ==============================================================================
# DYNAMIC REGISTRATION
# ==============================================================================

def register(cli):
    """
    Attaches the 'command' management group to the main CLI.
    """
    @cli.group(name="command")
    def command_group():
        """Manage CMC commands."""
        pass

    module_members = globals()
    for name, obj in module_members.items():
        if name.startswith("cmd_") and isinstance(obj, click.Command):
            command_group.add_command(obj)