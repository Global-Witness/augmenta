# augmenta

[![PyPI](https://img.shields.io/pypi/v/augmenta.svg)](https://pypi.org/project/augmenta/)
[![Tests](https://github.com/Global-Witness/augmenta/actions/workflows/test.yml/badge.svg)](https://github.com/Global-Witness/augmenta/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/Global-Witness/augmenta?include_prereleases&label=changelog)](https://github.com/Global-Witness/augmenta/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/Global-Witness/augmenta/blob/main/LICENSE)

AI-powered library for data enrichment using search results

## Installation

Install this library using `pip`:

```bash
pip install augmenta
```

## Usage

Normal run: `augmenta config.yaml`

Disable cache: `augmenta config.yaml --no-cache`

Resume process: `augmenta config.yaml --resume PROCESS_ID`

Clean old cache: `augmenta --clean-cache`

## Development

Create a new virtual environment:

```bash
cd augmenta
python -m venv venv
source venv/bin/activate
```

Now install the dependencies and test dependencies:

```bash
python -m pip install -e '.[test]'
```

To run the tests:

```bash
python -m pytest
```


## To-do
- [x] Refactor to async (use `aiohttp` for requests)
  - [x] Brave's free plan has a rate limit of 1 query/second, won't work with multithreading
- [x] Caching (for resuming interrupted augmentations) using SQLite
  - [ ] Remove the need to specify the config file to clean cache `augmenta --clean-cache`
  - [ ] More intelligent caching. Automatically offer to resume if interrupted (yes/no)
- [x] Progress bar for the CLI
- [ ] Test support for various models (Claude, Deepseek, etc)
- [ ] Validation of output for models wihtout a JSON schema
  - [ ] [Outlines](https://dottxt-ai.github.io/outlines/latest/welcome/) or [Instructor](https://python.useinstructor.com/)
  - [ ] If using Instructor, [extract directly to pandas](https://python.useinstructor.com/examples/pandas_df/)?
- [ ] Add LLM token limits, trimiing function
- [ ] Add support for other search engines (Oxylabs, Bing, etc)
- [ ] Scrape via proxy (oxylabs)
- [ ] Add [tests](https://python.useinstructor.com/examples/classification/#testing-and-evaluation)

### Nice to have
- [ ] Add support for PDFs and other file types?
- [ ] Keep logs (maybe as an option in the CLI?)
- [ ] Abstract examples in the YAML, add XML function
- [ ] Use chain-of-thought for more complex queries (or leave this to the user, but document it)
- [ ] Make it so that you can refer to other columns in the prompt