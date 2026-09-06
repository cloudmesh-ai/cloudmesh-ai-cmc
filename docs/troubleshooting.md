# Troubleshooting & FAQ

This guide provides solutions to common issues encountered when using or developing for `cloudmesh-ai-cmc`.

## Frequently Asked Questions

**Q: I installed a pip extension, but `cmc` doesn't see it.**
A: Ensure the package defines the `cloudmesh.ai.command` entry point in its `pyproject.toml` or `setup.py`. You can run `pip list` to verify that the package is correctly installed in your current environment.

**Q: I'm seeing "Click version mismatch" errors in debug logs.**
A: This is normal behavior. CMC uses the `DelegatingCommand` wrapper to isolate extensions, ensuring they execute correctly despite version differences in the `click` library.

**Q: How do I debug a failing `command load`?**
A: Run the command with the `CMC_LOG_LEVEL` environment variable set to `DEBUG`:
```bash
CMC_LOG_LEVEL=DEBUG cmc command load <path>
```
The logs will show exactly where the `importlib` failure occurred during the lazy-load attempt.

## Common Error Messages

| Error | Probable Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError` | Missing dependency in extension | Check the `dependencies` list in the extension metadata and install missing packages. |
| `Permission Denied` | Insufficient privileges for local registry | Ensure you have read/write access to the directory where the extensions are stored. |
| `Command not found` | Extension is registered but not activated | Run `cmc plugins enable <name>` to activate the extension. |
