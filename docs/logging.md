I want you to create a new `logging.py` file that will centralise the functionality of `logger` and `logfire` across my codebase in one place.

Logging should only be enabled when `verbose` is enabled in @/augmenta/cli.py

When logging is enabled, use `logger` to log messages as is the case now. If `logfire` is installed and configured, use `logfire` instead of `logger`.

When using `logfire`, I want you to create a new span for each row processed by `process_row()` in @/augmenta/core/augmenta.py . All the logs relevant to that row (API calls, extraction warnings) should be traced to that span.

Currently, all the logfire logs are displayed chronologically. Since this is an async process, each row is processed in parallel, and the logs are mixed up, making it difficult to trace them to their individual rows.

Please use the logfire documentation to implement proper tracing:
@https://logfire.pydantic.dev/docs/how-to-guides/distributed-tracing/
@https://logfire.pydantic.dev/docs/guides/onboarding-checklist/add-manual-tracing/

Only create one span per row. Keep all relevant code in `logging.py`, make only minimal changes to the other files. Keep it simple, I don't need any additional complexity. Follow the logfire documentation to the letter.