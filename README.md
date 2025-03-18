# augmenta

[![lifecycle](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://www.tidyverse.org/lifecycle/#experimental)
[![PyPI](https://img.shields.io/pypi/v/augmenta.svg)](https://pypi.org/project/augmenta/)
[![Tests](https://github.com/Global-Witness/augmenta/actions/workflows/test.yml/badge.svg)](https://github.com/Global-Witness/augmenta/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/Global-Witness/augmenta?include_prereleases&label=changelog)](https://github.com/Global-Witness/augmenta/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/Global-Witness/augmenta/blob/main/LICENSE)

Augmenta is a tool for enhancing datasets with search data, parsed by AI.

## Why?

Large Language Models (LLMs) are prone to [hallucinations](https://en.wikipedia.org/wiki/Hallucination_(artificial_intelligence)), making them unreliable sources of truth, particularly when it comes to tasks that require domain-specific knowledge.

Augmenta aims to address this by using search data to improve the reliability of the information provided by LLMs. This technique is known as "search-based [Retrieval-Augmented Generation (RAG)](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)", and has been shown to significantly improve output quality.

## Installation

First, make sure you have Python 3.8 or later and [`pipx`](https://pipx.pypa.io/latest/installation/#installing-pipx) installed on your computer.

Then, open your terminal and run the following command to install Augmenta:

```bash
pipx install git+https://github.com/Global-Witness/augmenta.git
```

You may wish to do this in a virtual environment to avoid conflicts with other Python packages. This will limit Augmenta's scope to the current directory.

```bash
python -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate
pip install git+https://github.com/Global-Witness/augmenta.git
```

## Usage

> [!TIP]
> If you would rather follow an example, [go here](/docs/examples/donations/README.md).

Create a new directory for your project and copy the data you want processed into it. Augmenta currently supports CSV files in a [tidy format](https://research-hub.auckland.ac.nz/managing-research-data/organising-and-describing-data/tidy-data).

### Configuration file

Create a new file called `config.yaml` and open it in your text editor. Your [YAML](https://en.wikipedia.org/wiki/YAML) file will instruct Augmenta on how you want to use it.

Here is an example of what it might look like:

```yaml
input_csv: original_data.csv
output_csv: processed_data.csv
model:
  name: openai/gpt-4o-mini
query_col: org
search:
  engine: brave
prompt:
  system: You are an expert at classifying companies.
  user: Please classify whether {{org}} is a for-profit company, and NGO, a government department, or something else.
structure:
  org_type:
    type: str
    description: What kind of organisation is it?
    options:
      - for-profit
      - NGO
      - government department
      - other
  other:
    type: str
    description: If other, what is it?
examples:
  - input: Microsoft
    output:
      org_type: for-profit company
  - input: Global Witness
    output:
      org_type: NGO
  - input: BBC
    output:
      org_type: other
      other: public service broadcaster
```

Let's break down what each of these fields means.

- `input_csv`: The name of the CSV file you want to augment. This file should be in the same project as your `config.yaml` file.
- `output_csv`: The name of the CSV file you want to create with the augmented data.
- `model`: The name of the LLM you want to use. You can find a list of supported models [here](https://ai.pydantic.dev/models/). Note that you need to provide both the provider and the model name (ie. `anthropic/claude-3.5-sonnet`).
- `query_col`: The name of the column in your input CSV that you want to use as the search query. Augmenta will retrieve results for each row in this column and use them to augment your data.
- `search`: The search engine you want to use. You can find a list of supported search engines [here](/docs/search.md).
- `prompt`: The instructions you want the AI to follow. You can use double curly braces (`{{ }}`) to refer to columns in your input CSV. Therea are some tips on writing good prompts [here](docs/prompt.md).
- `structure`: The structure of the output data. You can think of this as the columns you want added to your original CSV.
- `examples`: Examples of the output data. These will help the AI better understand what you're looking for.

### Credentials

If you use a search engine or LLM that requires an API key, you can set those in the YAML file.

```yaml
api_keys:
  BRAVE_API_KEY: "XXXXX"
  OPENAI_API_KEY: "XXXXX"
```

A better way to manage your credentials is to use environment variables. Create a new file called `.env` in the root directory of your project and add your credentials there.

```bash
BRAVE_API_KEY=XXXXX
OPENAI_API_KEY=XXXXX
```

This will keep your credentials out of your configuration file and make it easier to share your project with others, while keeping your keys to yourself.

### Running Augmenta

Save `config.yaml` and `.env`, and open a terminal window in the root directory of your project. Run `augmenta config.yaml` to get started.

By default, Augmenta will save your progress so that you can resume if the process gets interrupted at any point. You can find options for working with the cache [here](docs/cache.md).

To run Augmenta in verbose mode, use the `-v` flag: `augmenta -v config.yaml`. You can also add `LOGFIRE_SEND_TO_LOGFIRE=true` to your `.env` file to send logs to [logfire](https://logfire.pydantic.dev/), making it easier to observe what's happening.

## Read more

- [Choosing and configuring a search engine](/docs/search.md)
- [Writing a good prompt](/docs/prompt.md)
- [How caching works](/docs/cache.md)
- [An example in action](/docs/examples/donations/README.md)

## Development

Create a new virtual environment:

```bash
cd augmenta
python -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate
```

Now install the dependencies and test dependencies:

```bash
python -m pip install -e '.[test]'
```

To run the tests:

```bash
python -m pytest
```