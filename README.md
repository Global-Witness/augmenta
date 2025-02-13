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

First, make sure you have Python 3.8 or later installed on your computer.

Then, open your terminal and run the following command to install Augmenta:

```bash
pipx install git+https://github.com/Global-Witness/augmenta.git
```

## Usage

### Configuration file

Create a new directory for your project, copy the data you want processed into it, then create a new file called `config.yaml` and open it in your text editor. Your [YAML](https://en.wikipedia.org/wiki/YAML) file will instruct this tool on how you want to use it.

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
      other: Public service broadcaster
```

Let's break down what each of these fields means.

- `input_csv`: The name of the CSV file you want to augment. This file should be in the same directory as your `config.yaml` file.
- `output_csv`: The name of the CSV file you want to create with the augmented data.
- `model`: The name of the model you want to use for the AI. You can find a list of models [here](https://docs.litellm.ai/docs/providers).
- `query_col`: The name of the column in your input CSV that you want to use as the search query. Augmenta will retrieve results for each row in this column and use them to augment your data.
- `prompt`: The instructions you want the AI to follow. You can use double curly braces (`{{ }}`) to refer to columns in your input CSV. Therea are some tips on writing good prompts [here](docs/prompt.md).
- `structure`: The structure of the output data. You can think of this as the columns you want added to your original CSV.
- `examples`: Examples of the output data. These will help the AI better understand what you're looking for.

Save your YAML and open a terminal in the root directory of your project. You can then run `augmenta config.yaml` to get started.

By default, Augmenta will save your progress so that you can resume if the process gets interrupted at any point. You can find options for working with the cache [here](docs/cache.md).

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
