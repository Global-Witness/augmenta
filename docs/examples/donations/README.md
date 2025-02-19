# Electoral Commission donations data


The Electoral Commission [publishes
data](https://search.electoralcommission.org.uk/?currentPage=1&rows=100&sort=AcceptedDate&order=desc&tab=1&et=pp&et=ppm&et=tp&et=perpar&et=rd&isIrishSourceYes=true&isIrishSourceNo=true&prePoll=false&postPoll=true&register=gb&register=ni&register=none&optCols=Register&optCols=CampaigningName&optCols=AccountingUnitsAsCentralParty&optCols=IsSponsorship&optCols=IsIrishSource&optCols=RegulatedDoneeType&optCols=CompanyRegistrationNumber&optCols=Postcode&optCols=NatureOfDonation&optCols=PurposeOfVisit&optCols=DonationAction&optCols=ReportedDate&optCols=IsReportedPrePoll&optCols=ReportingPeriodName&optCols=IsBequest&optCols=IsAggregation)
on donations to political parties in the UK. This data contains some
information about the donor, such as their name and status, but not much
else.

This example shows how to use Augmenta to enrich this data with
additional information about the donors, such as their industry,
location, and size. This can help to identify patterns in donations,
such as which industries are more likely to donate to which parties.

## Data prep

``` r
library(tidyverse)
```

First, let’s download and read the data.

``` r
donations_raw <- read_csv("https://search.electoralcommission.org.uk/api/csv/Donations?start={start}&rows=100&query=&sort=AcceptedDate&order=desc&et=pp&date=Accepted&from=2024-07-01&to=2024-09-30&rptPd=&prePoll=false&postPoll=true&register=ni&register=gb&isIrishSourceYes=true&isIrishSourceNo=true&includeOutsideSection75=true")
```

For the purposes of this example, we’ll only keep the columns that
contain information about the donor. We’ll also only look at the first
10 rows to keep things simple.

``` r
donations <- donations_raw |>
  slice_head(n = 10) |>
  select(RegulatedEntityName, DonorName, DonorStatus, CompanyRegistrationNumber, Value) |>
  mutate(Value = parse_number(Value)) |>
  # remove duplicate rows
  group_by(RegulatedEntityName, DonorName, DonorStatus, CompanyRegistrationNumber) |>
  summarise(Value = sum(Value)) |>
  ungroup()
```

Finally, let’s save this data as a CSV file.

``` r
write_csv(donations, "data/donations.csv")
```

## Augmentation

Now that we have our data, we can use Augmenta to enrich it with
additional information about the donors.

## Setup

First, we need to configure our project. Create a new directory for you
project. In it, create a file called `config.yaml` and paste this into
it:

``` yaml
input_csv: data/donations.csv
output_csv: data/donations_classified.csv
model:
  name: openai/gpt-4o-mini
  max_tokens: 20000
query_col: DonorName
search:
  engine: brave
  country: GB
  results: 10
  rate_limit: 2
prompt:
  system: You are an expert researcher whose job is to classify individuals and companies based on their industry.
  user: |
    # Instructions

    The following documents are web search results about {{DonorName}}, a {{RegulatedEntityName}} donor identified in data published by the UK Electoral Commission. Your task is to determine what industry {{DonorName}} belongs to. The documents could be about a company, a trade group, a union, an individual, etc.
    
    If {{DonorName}} is an individual, you should classify them based on their profession or the industry they are closest associated with. If the documents are about multiple individuals, or if it's not clear which individual the documents refer to, please set the industry to "Don't know" and the confidence level to 1. For example, there's no way to know for certain that someone named "John Smith" in the documents is the same person as the donor in the Electoral Commission.

    We also know that the donor is a {{DonorStatus}}.

    Use the information provided in the documents to make your decision. Be critical, use common sense and respond only in English. Now, please proceed with your analysis and classification of {{DonorName}}.    
structure:
  chain_of_thought:
    type: str
    description: Understand the task and make a complete plan to accomplish it. Explain your reasoning. Then, carry out the plan, think of potential issues that might come up, then show your answer. Assess your own answer, think of ways to improve it, and then show the improved answer.
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
  confidence:
    type: int
    description: Your confidence level in the decision, on a scale of 1 (lowest) to 10 (highest). If you don't have enough information or the documents refer to different organisations that may share a name, please set this to 1.
examples:
  - input: "Charles A Daniel-Hobbs"
    output:
      industry: Financial and insurance activities
      explanation: |
        According to [the Wall Street Journal](https://www.wsj.com/market-data/quotes/SFNC/company-people/executive-profile/247375783), Mr. Charles Alexander DANIEL-HOBBS is the Chief Financial Officer and Executive Vice President of Simmons First National Corp, a bank holding company.
        
        A Charles Alexander DANIEL-HOBBS also operates several companies, such as [DIBDEN PROPERTY LIMITED](https://find-and-update.company-information.service.gov.uk/company/10126637), which Companies House classifies as "Other letting and operating of own or leased real estate". However, the information is not clear on whether these are the same person.
      confidence: 2
  - input: "Unite the Union"
    output:
      industry: Trade union
      explanation: |
        Unite is [one of the two largest trade unions in the UK](https://en.wikipedia.org/wiki/Unite_the_Union), with over 1.2 million members. It represents various industries, such as construction, manufacturing, transport, logistics and other sectors.
      confidence: 7
  - input: "Google UK Limited"
    output:
      industry: Information and communication
      explanation: |
        Google UK Limited is a [subsidiary of Google LLC](https://about.google/intl/ALL_uk/google-in-uk/), a multinational technology company that specializes in Internet-related services and products.

        The company [provides various web based business services](https://www.bloomberg.com/profile/company/1200719Z:LN), including a web based search engine which includes various options such as web, image, directory, and news searches. 
      confidence: 10
  - input: "John Smith"
    output:
      industry: Don't know
      explanation: |
        The documents about John Smith refer to multiple people, so there's no way to accurately assess what industry this particular individual belongs to.
      confidence: 1
```

A few things to note about the configuration:

- We’re using Brave due to its generous free API tier, but Google search
  results are generally more accurate.
- Because our dataset is UK-centric, we’re setting the country to “GB”
  in Brave. This should help filter out some of the irrelevant results.
- The industries are based on the [Standard Industrial
  Classification](https://resources.companieshouse.gov.uk/sic/) groups.
  You can probably come up with something more clever.
- We are using chain-of-thought to guide the model through the process
  of classification. This can help improve accuracy.

Because we’re using Brave and an OpenAI model, we need API keys for both
services. Save them to a file called `.env` in the root of your project
directory:

    BRAVE_API_KEY=YOUR_KEY_GOES_HERE
    OPENAI_API_KEY=YOUR_KEY_GOES_HERE

## Running the augmentation

Make sure you have `augmenta`
[installed](https://github.com/Global-Witness/augmenta/tree/main?tab=readme-ov-file#installation),
open the terminal and navigate to the directory where you saved the
data, configuration file and API keys.

Run the following command to start the classification.

``` bash
augmenta config.yaml
```

This should take a few seconds. Once it’s done, you’ll have a new file
called `data/donations_classified.csv` with the augmented data.

``` r
library(gt)

read_csv("data/donations_classified.csv") |>
  select(-DonorStatus, -CompanyRegistrationNumber, -chain_of_thought) |>
  gt() |>
  fmt_markdown(columns = "explanation")
```

    Rows: 9 Columns: 9
    ── Column specification ────────────────────────────────────────────────────────
    Delimiter: ","
    chr (6): RegulatedEntityName, DonorName, DonorStatus, chain_of_thought, indu...
    dbl (3): CompanyRegistrationNumber, Value, confidence

    ℹ Use `spec()` to retrieve the full column specification for this data.
    ℹ Specify the column types or set `show_col_types = FALSE` to quiet this message.

| RegulatedEntityName | DonorName | Value | industry | explanation | confidence |
|----|----|----|----|----|----|
| Labour Party | Labour Together Limited | 53824.20 | Professional, scientific and technical activities | Labour Together Limited is a think tank that focuses on developing political policy and measuring public opinion, closely associated with the Labour Party. It was founded in June 2015 and operates as a private company limited by guarantee without share capital. The nature of its business is classified under SIC code 94990, which pertains to activities of other membership organizations not elsewhere classified. This classification aligns with the operations of a think tank, which typically engages in research and policy development. Therefore, it is classified under the industry of ‘Professional, scientific and technical activities’. | 8 |
| Labour Party | The Good Faith Partnership LLP | 15660.00 | Professional, scientific and technical activities | The Good Faith Partnership LLP operates as a social consultancy, engaging with various sectors including government, charities, and businesses to tackle complex societal issues. Their work involves convening leaders from different fields to foster collaboration and develop innovative solutions, which is characteristic of the professional services industry. They are also members of The Public Relations and Communications Association (PRCA), indicating their involvement in public relations and communications, further supporting their classification in the professional services sector. Their focus on cross-sector initiatives and public policy aligns with the ‘Professional, scientific and technical activities’ industry classification. For more information, you can visit their <a href="https://goodfaith.org.uk">website</a>. | 8 |
| Liberal Democrats | JOHN HEMMING TRADING LIMITED | 1000.00 | Arts, entertainment and recreation | JOHN HEMMING TRADING LIMITED is classified under the SIC code 90040, which corresponds to the ‘Operation of arts facilities’. This indicates that the company is involved in activities related to the arts and entertainment sector. The registered office is located in Birmingham, and the company has been active since its incorporation in 2011. The nature of business aligns with the arts industry, which includes various forms of artistic expression and facilities that support such activities. Therefore, it is reasonable to conclude that the company operates within the arts, entertainment, and recreation industry. | 9 |
| Liberal Democrats | Patricia Bell | 2790.00 | Don't know | The documents refer to multiple individuals named Patricia Bell, including a politician, an author, and a retired management consultant. Without clear identification of which Patricia Bell is the donor, it is impossible to accurately classify her industry. Therefore, I classify her as “Don’t know” with a confidence level of 1. | 1 |
| Liberal Democrats | Robert H Miall | 2500.00 | Arts, entertainment and recreation | Robert H Miall is identified as a writer, with a bibliography that includes science fiction and television tie-in novels. According to <a href="https://www.worldswithoutend.com/author.asp?ID=3797">Worlds Without End</a>, he was born in 1922 and passed away in 2011, and his works include titles related to the UFO genre. This clearly places him in the arts and entertainment sector, specifically in literature. Therefore, the most appropriate industry classification for Robert H Miall is ‘Arts, entertainment and recreation’. | 9 |
| Liberal Democrats | Scottish Parliament. | 4376.10 | Public administration and defence; compulsory social security | The Scottish Parliament is the legislative body of Scotland, responsible for making laws and overseeing the Scottish Government. It was established in 1999 following a referendum that supported devolution. The Parliament has the authority to legislate on various devolved matters, including health, education, and justice, which are essential functions of public administration. As a public institution, it operates within the framework of government and public service, making it a key player in the public administration sector. This classification aligns with its role in governance and public policy-making in Scotland. | 9 |
| Liberal Democrats | Stephen F Gosling | 2500.00 | Don't know | The documents refer to multiple individuals named Stephen Gosling, including a professional photographer and a pianist, but do not provide clear information linking them to the donor identified by the UK Electoral Commission. Therefore, it is not possible to accurately classify Stephen F Gosling into a specific industry based on the available information. | 1 |
| Liberal Democrats | Wirral Liberal Club | 127709.80 | Political group | The Wirral Liberal Club is a trust associated with the Liberal Democrats, indicating its role as a political organization. It functions as a social club for members of the Liberal Party, providing a space for political discussion and community engagement. The club’s activities are closely tied to political advocacy and support for liberal values, which aligns it with the ‘Political group’ industry. This classification is supported by its historical context and current operations as a venue for political gatherings and discussions. | 8 |
| Ulster Unionist Party | Northern Ireland Assembly | 7069.03 | Public administration and defence; compulsory social security | The Northern Ireland Assembly serves as the devolved legislature for Northern Ireland, responsible for making laws on a wide range of issues including health, education, and agriculture. It operates under the framework established by the Good Friday Agreement and is a key institution in the governance of Northern Ireland. The Assembly is composed of elected Members of the Legislative Assembly (MLAs) who represent the public and scrutinize the work of the government. Given its legislative and governance functions, it is classified under public administration. More information can be found on the official <a href="https://www.niassembly.gov.uk/">Northern Ireland Assembly website</a>. | 9 |

</div>

## Results

There are a few things to note here.

First, the results are only as good [as the information they’re
fed](https://en.wikipedia.org/wiki/Garbage_in%2C_garbage_out). Google
search results tend to be better than those offered by Brave or
Duckduckgo, but they’re not perfect either.

This is particularly an issue with individuals with generic names. We
have instructed the model to flag those cases as “Don’t know”, but it
can still lead to some issues.

For example, the “Robert H Miall” identified in the search results has
passed away in 2011 (as noted by the LLM itself), so he can’t be the
donor we’re looking for (the donations are from 2024).

We can work around these limitations in a few ways:

- Increase the number of results to get a better picture of the donor.
- Use a better search engine and/or more specific search query.
- Be more descriptive about these edge cases in the prompt and examples.
- Filter out individual donors and stick to organisations.

For organisations, which tend to be easier to identify, the model does a
much better job.

If we were to publish any analysis of this data, we would need to
fact-check the results.
