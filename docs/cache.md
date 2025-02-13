# Caching progress

Augmenta saves your progress to a SQLite database so that you can resume interrupted augmentations. The database is stored in the `.augmenta` directory in the root of your project.

If a process gets interrupted, for example if you cancel it or the internet connection is lost, you can resume it by running the same command (like `augmenta config.yaml`) you initially did. If no changes were made to the configuration YAML or the original CSV, Augmenta will ask whether you want to pick up where you left off.

If you want to run the process without saving progress, you can run `augmenta config.yaml --no-cache`.

To resume a process by its ID (found in `cache.db`), you can run `augmenta config.yaml --resume PROCESS_ID`.

To clean up the cache and start fresh, delete the `cache.db` file or run `augmenta --clean-cache`.