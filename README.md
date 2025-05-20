# augmenta

[![lifecycle](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://www.tidyverse.org/lifecycle/#experimental)
[![PyPI](https://img.shields.io/pypi/v/augmenta.svg)](https://pypi.org/project/augmenta/)
[![Tests](https://github.com/Global-Witness/augmenta/actions/workflows/test.yml/badge.svg)](https://github.com/Global-Witness/augmenta/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/Global-Witness/augmenta?include_prereleases&label=changelog)](https://github.com/Global-Witness/augmenta/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/Global-Witness/augmenta/blob/main/LICENSE)

Augmenta is an AI agent for enhancing datasets with information from the internet (and [more](/docs/tools.md)).

## Why?

Large Language Models (LLMs) can be powerful tools for processing a lot of information very quickly. However, they don't do it entirely accurately. LLMs are prone to [hallucinations](https://en.wikipedia.org/wiki/Hallucination_(artificial_intelligence)), making them unreliable sources of truth, particularly when it comes to tasks that require domain-specific knowledge.

Augmenta aims to address this shortcoming by allowing LLMs to search and browse the internet for information. This technique is known as "search-based [Retrieval-Augmented Generation (RAG)](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)", or "[grounding](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/grounding-llms/3843857)", and has been shown to significantly improve output quality. It does not, however, eliminate the risk of hallucinations entirely, so you should always verify the results before publishing them.

## Installation

<details>

<summary>Install with uv/uvx (recommended)</summary>

If you're using [uv](https://docs.astral.sh/uv/), open your terminal and run the following command to install Augmenta:

```bash
uvx install git+https://github.com/Global-Witness/augmenta.git
```

You may wish to do this in a virtual environment to avoid conflicts with other Python packages. This will limit Augmenta's scope to the current directory.

```bash
uv venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate
uv pip install git+https://github.com/Global-Witness/augmenta.git
```

</details>

<details>

<summary>Install with pip/pipx</summary>

First, make sure you have Python 3.10 or later and [`pipx`](https://pipx.pypa.io/latest/installation/#installing-pipx) installed on your computer.

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

</details>


## Usage

> [!TIP]
> If you would rather follow an example, [go here](https://github.com/Global-Witness/orcl?tab=readme-ov-file#augmenta).

Start by creating a new directory for your project. This will contain all your data, configuration files, as well as some temporary files that Augmenta will create while it runs.

Copy the data you want processed into this directory (or a subdirectory). Augmenta currently supports CSV files in a [tidy format](https://research-hub.auckland.ac.nz/managing-research-data/organising-and-describing-data/tidy-data), where each row will contain an entity you want to process (eg. company), and each column will contain a different attribute of that entity (eg. industry, address, revenue, etc.).

### Configuration file

The LLM needs instructions on how to process your data. Create a new file called `config.yaml` (you can change the name if you prefer) somewhere in your project directory and open it with a text editor. Copy this into it:

```yaml
input_csv: path/to/original_data.csv
output_csv: path/to/processed_data.csv
model:
  provider: openai
  name: gpt-4o-mini
search:
  engine: brightdata_google
prompt:
  system: You are an expert researcher whose job is to classify organisations based on the industry they belong to.
  user: |
    # Instructions

    Your job is to research "{{DonorName}}", a donor to a political party in the UK. Your will determine what industry {{DonorName}} belongs to. The entity could be a company, a trade group, a union, an individual, etc.
    
    If {{DonorName}} is an individual, you should classify them based on their profession or the industry they are closest associated with. If the documents are about multiple individuals, or if it's not clear which individual the documents refer to, please set the industry to "Don't know" and the confidence level to 1. For example, there's no way to know for certain that someone named "John Smith" in the documents is the same person as the donor in the Electoral Commission.

    We also know that the donor is a {{DonorStatus}}.

    ## Searching guidelines

    In most cases, you should start by searching for {{DonorName}} without any additional parameters. Where relevant, remove redundant words like "company", "limited", "plc", etc from the search query. If you need to perform another search, try to refine it by adding relevant keywords like "industry", "job", "company", etc. Note that each case will be different, so be flexible and adaptable. Unless necessary, limit your research to two or three searches.

    With each search, select a few sources with `mcp-server-fetch-python` that are most likely to provide relevant information. Access them using the tools provided. Be critical and use common sense. ALWAYS cite your sources.
    
    Now, please proceed with your analysis and classification of {{DonorName}}.
structure:
  industry:
    type: str
    description: What industry is this organisation or person associated with?
    options:
      - Agriculture, Forestry and Fishing
      - Mining and Quarrying
      - Manufacturing
      - Electricity, gas, steam and air conditioning supply
      - Water supply, sewerage, waste management and remediation activities
      - Construction
      - Wholesale and retail trade; repair of motor vehicles and motorcycles
      - Transportation and storage
      - Accommodation and food service activities
      - Information and communication
      - Financial and insurance activities
      - Real estate activities
      - Professional, scientific and technical activities
      - Administrative and support service activities
      - Public administration and defence; compulsory social security
      - Education
      - Human health and social work activities
      - Arts, entertainment and recreation
      - Political group
      - NGO or think-tank
      - Trade union
      - Other
      - Don't know
  explanation:
    type: str
    description: A few paragraphs explaining your decision in English, formatted in Markdown. In the explanation, link to the most relevant sources from the provided documents. Include at least one inline URL.
examples:
  - input: "Charles A Daniel-Hobbs"
    output:
      industry: Financial and insurance activities
      explanation: |
        According to [the Wall Street Journal](https://www.wsj.com/market-data/quotes/SFNC/company-people/executive-profile/247375783), Mr. Charles Alexander DANIEL-HOBBS is the Chief Financial Officer and Executive Vice President of Simmons First National Corp, a bank holding company.
        
        A Charles Alexander DANIEL-HOBBS also operates several companies, such as [DIBDEN PROPERTY LIMITED](https://find-and-update.company-information.service.gov.uk/company/10126637), which Companies House classifies as "Other letting and operating of own or leased real estate". However, the information is not clear on whether these are the same person.
  - input: "Unite the Union"
    output:
      industry: Trade union
      explanation: |
        Unite is [one of the two largest trade unions in the UK](https://en.wikipedia.org/wiki/Unite_the_Union), with over 1.2 million members. It represents various industries, such as construction, manufacturing, transport, logistics and other sectors.
  - input: "Google UK Limited"
    output:
      industry: Information and communication
      explanation: |
        Google UK Limited is a [subsidiary of Google LLC](https://about.google/intl/ALL_uk/google-in-uk/), a multinational technology company that specializes in Internet-related services and products.

        The company [provides various web based business services](https://www.bloomberg.com/profile/company/1200719Z:LN), including a web based search engine which includes various options such as web, image, directory, and news searches. 
  - input: "John Smith"
    output:
      industry: Don't know
      explanation: |
        The documents about John Smith refer to multiple people (a [British polician](https://en.wikipedia.org/wiki/John_Smith_(Labour_Party_leader)), an [explorer](https://en.wikipedia.org/wiki/John_Smith_(explorer)), a [singer-songwriter](https://johnsmithjohnsmith.com/)), so there's no way to accurately assess what industry this particular individual belongs to.
```

You will need to edit this file to suit your project. Let's break all this down:

- `input_csv` and `output_csv` are the names of the data you want to process and where you want to save the results, respectively.
- `model`: The LLM you want to use. You can find a list of supported models [here](https://ai.pydantic.dev/models/). Note that you need to provide both a `provider` and model `name` (ie. `anthropic` and `claude-3.5-sonnet`). You will also likely need to set up an API key (see [credentials below](#credentials)).
- `search`: The search engine you want to use. You can find a list of supported search engines [here](/docs/search.md). You will also likely need to set up an API key here (see [credentials](#credentials)).
- `prompt`: LLMs take in a [system prompt](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts) and a user prompt. Think of the system prompt as explaining to the LLM what its role is, and the user prompt as the instructions you want it to follow. You can use double curly braces (`{{ }}`) to refer to columns in your input CSV. Therea are some tips on writing good prompts [here](docs/prompt.md).
- `structure`: The structure of the output data. You can think of this as the columns you want added to your original CSV.
- `examples`: Examples of the output data. These will help the AI better understand what you're trying to do.

### Credentials

You don't want to store API keys in your configuration file, as they are meant to be kept secret and it would make it less safe to share your project with others. Instead, you can use environment variables to store your credentials.

Create a new file called `.env` (just the extension, no file name) in the root directory of your project. Open it in a text editor and add your credentials there. They can look something like this, depending on the services you are using:

```bash
OPENAI_API_KEY=XXXXX
BRIGHTDATA_API_KEY=XXXXX
BRIGHTDATA_ZONE=XXXXX
```

### Running Augmenta

Make sure you have saved both your `config.yaml` and `.env` files. Open a **new** terminal window in the root directory of your project and run the following command:

```bash
augmenta config.yaml
```

It might be a few seconds before you see any output, but once it does, you will see a progress bar.

By default, Augmenta will save your progress so that you can resume if the process gets interrupted at any point. You can find options for working with the cache [here](docs/cache.md).

Start with a subset of your data (5-10 rows) to test your configuration and that you are happy with the results. [Adjust your prompt often](docs/prompt.md). You can then rerun Augmenta on the full dataset.

#### Monitoring

One issue with LLMs is that they are non-deterministic. Compared to traditional software, where you can expect the same input to produce the same predictable output every time, AI models are black boxes.

Augmenta uses `logfire` to observe how processes are running. [Sign up for a free account](https://logfire.pydantic.dev/) and make sure you have it [set up on your device](https://logfire.pydantic.dev/docs/).

Add `logfire: true` to your YAML and run Augmenta in verbose mode:

```bash
augmenta -v config.yaml
```

If everything is set up correctly, you should have a link to your logfire dashboard in the terminal. You will be able to monitor how Augmenta is running, which tools are using, any potential errors or inconsistencies, etc.

![Screenshot of a Logfire dashboard showing an Augmenta run](docs/logfire-demo.png "Logfire demo")

## Read more

- [Choosing and configuring a search engine](/docs/search.md)
- [Adding new tools to Augmenta](/docs/tools.md)
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