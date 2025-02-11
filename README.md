# augmenta

[![lifecycle](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://www.tidyverse.org/lifecycle/#experimental)
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
  - [x] Remove the need to specify the config file to clean cache `augmenta --clean-cache`
  - [ ] Fix the bug where it sometimes reads in a completed cache. Or maybe chech if the CSV has changed as well?
  - [ ] More intelligent caching. Automatically offer to resume if interrupted (yes/no)
- [x] Progress bar for the CLI
- [x] Validation of output
  - [x] [Instructor](https://python.useinstructor.com/) for models wihtout a JSON schema
  - [x] Remove output from the prompt
  - [x] Declare [possible outputs](https://python.useinstructor.com/concepts/enums/) in the YAML
- [x] Add LLM token limits, triming function, rate limiting
- [ ] Add support for other search engines (Oxylabs, Bing, etc)
- [ ] Tests
  - [ ] Add [tests](https://python.useinstructor.com/examples/classification/#testing-and-evaluation)
  - [ ] Test support for various models (Claude, Deepseek, etc) 
- [ ] Check for proper package structure stuff
- [ ] Documentation, examples, etc

### Nice to have
- [ ] Add support for PDFs and other file types?
- [ ] Keep logs (maybe as an option in the CLI?)
- [x] Abstract examples in the YAML, add XML function
- [ ] Use chain-of-thought for more complex queries (or leave this to the user, but document it)
- [ ] Allow the LLM to set/refine their own search queries
- [x] Make it so that you can refer to other columns in the prompt
- [ ] Make the search optional, some prompts may only need data that is already available in other columns
- [ ] Scrape via proxy (oxylabs)
- [ ] Cost (and [energy](https://huggingface.co/blog/sasha/announcing-ai-energy-score)?) tracker