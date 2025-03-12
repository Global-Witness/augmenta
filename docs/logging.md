I want to remove `logger` from my project and use `logfire` exclusively. I currently have some logging in my project using the @/augmenta/utils/logging.py module.

Remove all unnecessary code from there. Maybe remove the file altogether if it's not needed anymore.

Instead, let's implement logging in @/augmenta/core/augmenta.py. Logging (`logfire`) should only be enabled when `verbose` is enabled in @/augmenta/cli.py

In @/augmenta/core/llm/base.py , configure it based on the Pydantic AI docs: @https://logfire.pydantic.dev/docs/integrations/llms/pydanticai/