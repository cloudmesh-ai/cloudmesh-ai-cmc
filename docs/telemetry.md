# Telemetry & Observability

`cloudmesh-ai-cmc` includes a built-in telemetry system to track AI tool performance, reliability, and system context across all command executions.

## Overview

Telemetry data is automatically captured whenever a `cmc` command is executed. This data is essential for benchmarking AI models, debugging failures, and monitoring the efficiency of the ecosystem.

## Tracked Metrics

Every command execution captures a standardized set of metrics:

- **Duration**: Total execution time in seconds (`duration_sec`).
- **Status**: The final state of the command: `started`, `completed`, or `failed`.
- **System Context**: Hardware details including CPU model, GPU presence/model, and total memory.
- **Custom KPIs**: Extensions can pass their own specific metrics (e.g., tokens per second, accuracy) to the telemetry sink.

## Storage Backends

Telemetry data can be routed to multiple sinks depending on the required analysis:

- **JSONL**: Structured logs optimized for machine ingestion and streaming.
- **SQLite**: Relational storage allowing for complex SQL querying and aggregation.
- **Text**: Human-readable logs intended for quick debugging and manual review.

## Control and Configuration

You can manage telemetry via the CLI:
- Enable: `cmc telemetry on`
- Disable: `cmc telemetry off`
- List records: `cmc telemetry list`

To disable telemetry globally across all sessions, set the following environment variable:
```bash
CLOUDMESH_AI_TELEMETRY_DISABLED=true
```
