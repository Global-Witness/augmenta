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
    The following documents contain information extracted from a web search for "{{DonorName}}". Your task is to determine what industry {{DonorName}} belongs to. The documents could be about a company, a trade group, a union, or an individual. In the case of an individual, you should classify them based on their profession or the industry they are closest associated with.

    We also know that the donor is a {{DonorStatus}}.

    Use the information provided in the documents to make your decision. Be critical, use common sense and respond only in English. Now, please proceed with your analysis and classification of {{DonorName}}.
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
```

A few things to note about the configuration:

- We’re using Brave due to its generous free API tier, but Google search
  results are generally more accurate.
- Because our dataset is UK-centric, we’re setting the country to “GB”
  in Brave. This should help to filter some of the irrelevant results.
- The industries are based on the [Standard Industrial
  Classification](https://resources.companieshouse.gov.uk/sic/) groups.
  You can probably come up with something more clever.

Because we’re using Brave and an OpenAI model, we need API keys for both
services. Save them to a file called `.env` in the root of your project
directory:

    BRAVE_API_KEY=YOUR_KEY_GOES_HERE
    OPENAI_API_KEY=YOUR_KEY_GOES_HERE

## Running the augmentation

Make sure you have `augmenta` [installed](https://github.com/Global-Witness/augmenta/tree/main?tab=readme-ov-file#installation), open the
terminal and navigate to the directory where you saved the data,
configuration file and API keys.

Run the following command to start the classification.

``` bash
augmenta config.yaml
```

This should take a few seconds. Once it’s done, you’ll have a new file
called `data/donations_classified.csv` with the augmented data.

``` r
library(gt)

read_csv("data/donations_classified.csv") |>
  select(-DonorStatus, -CompanyRegistrationNumber) |>
  gt() |>
  fmt_markdown(columns = "explanation")
```

    Rows: 9 Columns: 8
    ── Column specification ────────────────────────────────────────────────────────
    Delimiter: ","
    chr (5): RegulatedEntityName, DonorName, DonorStatus, industry, explanation
    dbl (3): CompanyRegistrationNumber, Value, confidence

    ℹ Use `spec()` to retrieve the full column specification for this data.
    ℹ Specify the column types or set `show_col_types = FALSE` to quiet this message.


| RegulatedEntityName | DonorName | Value | industry | explanation | confidence |
|----|----|----|----|----|----|
| Labour Party | Labour Together Limited | 53824.20 | NGO or think-tank | Labour Together Limited operates as a think tank closely associated with the Labour Party in the UK. It was founded in 2015 to support Labour’s electoral strategies and contribute to policy development. Labour Together aims to provide innovative ideas and public policy research aligned with the Labour Party’s objectives, enhancing its electability. This is supported by various documents indicating their projects, reports, and their role in internal party dynamics as a means to significantly influence Labour’s political strategies. As such, its classification primarily aligns with the ‘NGO or think-tank’ category. More about Labour Together can be found on their official website <a href="https://www.labourtogether.uk/">Labour Together</a>. | 9 |
| Labour Party | The Good Faith Partnership LLP | 15660.00 | Professional, scientific and technical activities | The Good Faith Partnership LLP operates as a social consultancy, working to connect businesses, governments, charities, and communities to tackle societal issues through collaboration. Their work involves engaging with a diverse set of stakeholders including political leaders and community representatives to bring about meaningful change. They are involved in public affairs, public policy, and strategic initiatives, as indicated on their website <a href="https://goodfaith.org.uk">Good Faith Partnership</a>. Their focus on cross-sector initiatives aligns with the Professional, scientific and technical activities category, as they emphasize the importance of strategic communication and collaboration which are hallmarks of a consultancy firm. | 8 |
| Liberal Democrats | JOHN HEMMING TRADING LIMITED | 1000.00 | Arts, entertainment and recreation | JOHN HEMMING TRADING LIMITED is classified under the SIC code 90040, which pertains to the operation of arts facilities. The company is described as an active private limited company incorporated in 2011 and is based in Birmingham. The nature of the business indicates involvement in the arts sector, specifically in managing or operating facilities related to arts activities. This classification aligns with the information available from reliable sources such as Companies House and other business directories. Therefore, the industry associated with this company is clearly in the arts and recreation sector. | 9 |
| Liberal Democrats | Patricia Bell | 2790.00 | Professional, scientific and technical activities | Patricia Bell is an individual who holds multiple professional roles and has been involved in significant community and advisory capacities. She is currently identified as the Cabinet Member for Adult Care and has several committee appointments related to health and wellbeing, indicating her active engagement in public administration pertaining to health services. Additionally, she is a strong advocate in various health and social work committees aimed at improving community care and support. These responsibilities position her within the professional domain related to public service and healthcare. For more detailed information about her current roles, you can refer to <a href="https://westmorlandandfurness.moderngov.co.uk/mgUserInfo.aspx?UID=169">Westmorland and Furness Council</a>. | 8 |
| Liberal Democrats | Robert H Miall | 2500.00 | Arts, entertainment and recreation | Robert H Miall is primarily a writer, known for his works in science fiction and television tie-ins, as indicated by his publications such as ‘UFO’ and others that relate closely to the entertainment sector. His works have gained some recognition in literary databases and are available on platforms like Goodreads and Amazon, which categorize him as an author, emphasizing his contributions to literature and entertainment. Miall’s background suggests that he worked within the realm of the arts, particularly in writing for television series and book adaptations, aligning him with the industry of arts, entertainment, and recreation. | 8 |
| Liberal Democrats | Scottish Parliament. | 4376.10 | Public administration and defence; compulsory social security | The Scottish Parliament is the unicameral legislature of Scotland, which is responsible for law-making and overseeing the Scottish government. It operates under a devolved government system established by the Scotland Act 1998, which delegated powers from the UK Parliament to the Parliament of Scotland. The Scottish Parliament handles various powers related to public administration including health, education, justice, and transport. This aligns it with the political and public administration sectors. Its role in representing and legislating for Scottish interests categorizes it firmly within the public sector of governmental activities. More details can be found on the <a href="https://www.parliament.scot/">Scottish Parliament website</a>. | 9 |
| Liberal Democrats | Stephen F Gosling | 2500.00 | Arts, entertainment and recreation | Stephen F. Gosling is primarily associated with the arts, specifically as a pianist and a performer within the contemporary music scene. His performances span numerous notable venues and festivals across various continents, and he is recognized for his contributions to modern classical music as a member of various ensembles, including the American Modern Ensemble. Publications such as the New York Times and the Washington Post have spotlighted his artistry, demonstrating his significant role in the arts community. This categorization aligns with the information available from distinguished sources like <a href="https://americanmodernensemble.org/stephen-gosling-piano">American Modern Ensemble</a>, which showcases his contributions to contemporary music. | 8 |
| Liberal Democrats | Wirral Liberal Club | 127709.80 | Accommodation and food service activities | The Wirral Liberal Club was a social club and public house located in Oxton, Merseyside. According to the information provided, it had a full pub license, which indicates that it was involved in serving food and beverages, thus classifying it under the accommodation and food service activities industry. However, the club has long-term closed since April 2019, and its premises underwent a change of use to residential apartments. Although the club itself is no longer operating, it was primarily associated with hospitality services before its closure, making this classification relevant. Sources: <a href="https://whatpub.com/pubs/WIR/333/wirral-liberal-club-oxton">WhatPub</a>, <a href="https://www1.camra.org.uk/pubs/wirral-liberal-club-oxton-132116">CAMRA</a>. | 8 |
| Ulster Unionist Party | Northern Ireland Assembly | 7069.03 | Public administration and defence; compulsory social security | The Northern Ireland Assembly is a devolved legislature responsible for making laws and scrutinizing the work of ministers and government departments on various transferred matters such as health, education, and agriculture. As the governing body of Northern Ireland, it plays a crucial role in public administration. According to the <a href="https://www.niassembly.gov.uk/">Northern Ireland Assembly’s official website</a>, the assembly has the authority to legislate in a wide range of areas not reserved to the UK Parliament, focusing on local governance and public services. Its nature as a public institution aligns it closely with the public administration sector. | 8 |

</div>

## Results

There are a few things to note here.

First, the results are only as good [as the information they’re
fed](https://en.wikipedia.org/wiki/Garbage_in%2C_garbage_out). Google
search results tend to be better than those offered by Brave or
Duckduckgo, but they’re not perfect either.

This is particularly an issue with individuals with generic names. For
example, it’s likely that Patricia Bell in the dataset is not the
University of Georgia professor surfaced by the search engine and
classified by the LLM. This doesn’t stop the LLM from offering a high
degree of confidence in its classification.

We can work around these limitations in a few ways:

- Increase the number of results to get a better picture of the donor.
- Use a better search engine and/or more specific search query.
- Be more descriptive about these edge cases in the prompt and examples.
- Filter out individual donors and stick to organisations.

For organisations, which tend to be easier to identify, the model does a
much better job.

If we were to publish any analysis of this data, we would need to
fact-check the results.
