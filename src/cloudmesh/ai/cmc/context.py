# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
import os
import logging
from cloudmesh.ai.common import logging as ai_log
from cloudmesh.ai.common.telemetry import Telemetry, JSONFileBackend, TextBackend
from cloudmesh.ai.cmc.utils import Config

# Initialize Configuration
config = Config()

# Setup Logging
log_level = os.getenv("CMC_LOG_LEVEL", config.get("logging.level", "WARNING")).upper()
logger = ai_log.get_logger("cmc")
logger.setLevel(getattr(logging, log_level, logging.WARNING))

# Initialize Telemetry based on config
telemetry_enabled = config.get("telemetry.enabled", True)
telemetry_path = os.path.expanduser(config.get("telemetry.path", "~/cmc_telemetry.jsonl"))

if not telemetry_enabled:
    os.environ["CLOUDMESH_AI_TELEMETRY_DISABLED"] = "true"

backends = []
if telemetry_enabled:
    backends.append(JSONFileBackend(telemetry_path))
    if os.getenv("CMC_DEBUG") == "1" or log_level == "DEBUG":
        backends.append(TextBackend())

telemetry = Telemetry(command_name="cmc", backends=backends)