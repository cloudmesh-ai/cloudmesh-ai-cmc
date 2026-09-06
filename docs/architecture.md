# Architecture

The `cloudmesh-ai-cmc` framework is designed to maintain a small memory footprint while supporting a vast library of extensions through a delegating registry.

## Core Design

Rather than loading every available extension into memory at startup, `cmc` uses a "lazy loading" approach. Commands are registered in a registry but only imported when actually called by the user.

### Execution Flow

``` mermaid
graph TD
    A[User Input: cmc <cmd>] --> B[SubcommandHelpGroup]
    B --> C{Is Command Lazy?}
    C -- Yes --> D[LazyCommand Registry]
    D --> E[importlib.import_module]
    E --> F[DelegatingCommand Wrapper]
    C -- No --> G[Direct Execution]
    F --> H[Extension Logic]
    G --> H
```

## The DelegatingCommand Wrapper

A key component of the architecture is the `DelegatingCommand` wrapper. This wrapper is critical for stability in an ecosystem where extensions may be developed and compiled against different versions of the `click` library.

By isolating the core framework from the extensions, the `DelegatingCommand` prevents runtime type-mismatch crashes and ensures that the main CLI remains stable regardless of the specific dependencies of a particular plugin.
