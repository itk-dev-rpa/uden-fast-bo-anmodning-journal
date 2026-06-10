"""Local debug entry point for running the robot outside OpenOrchestrator's Scheduler.

Reads the OpenOrchestrator connection settings from a local ``.env`` file (see
``.env.example``) and runs the process directly. This bypasses the retry loop and
the error-screenshot handling in ``linear_framework.main()``, so you can set
breakpoints in ``process.py`` and step straight into the logic.

For local debugging only. In production the robot is started with
``python -m robot_framework`` by the Scheduler.
"""

import os

from dotenv import load_dotenv
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import initialize, process


def main() -> None:
    """Build a connection from the .env file and run the process once."""
    load_dotenv()

    # trigger_id and job_id must be valid UUID strings or None. OpenOrchestrator
    # calls UUID() on them when logging, so empty strings are coerced to None.
    orchestrator_connection = OrchestratorConnection(
        os.environ["OO_PROCESS_NAME"],
        os.environ["OO_CONNECTION_STRING"],
        os.environ["OO_CRYPTO_KEY"],
        os.getenv("OO_PROCESS_ARGS", ""),
        os.getenv("OO_TRIGGER_ID") or None,
        os.getenv("OO_JOB_ID") or None,
    )

    initialize.initialize(orchestrator_connection)
    process.process(orchestrator_connection)


if __name__ == "__main__":
    main()
