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
donations_raw <- read_csv(
    "https://search.electoralcommission.org.uk/api/csv/Donations?start={start}&rows=100&query=&sort=AcceptedDate&order=desc&et=pp&date=Accepted&from=2024-07-01&to=2024-09-30&rptPd=&prePoll=false&postPoll=true&register=ni&register=gb&isIrishSourceYes=true&isIrishSourceNo=true&includeOutsideSection75=true"
)
```

For the purposes of this example, we’ll only keep the columns that
contain information about the donor. We’ll also only look at the first
10 rows to keep things simple.

``` r
donations <- donations_raw |>
    slice_sample(n = 5) |>
    select(
        RegulatedEntityName,
        DonorName,
        DonorStatus,
        CompanyRegistrationNumber,
        Value
    ) |>
    mutate(Value = parse_number(Value)) |>
    # remove duplicate rows
    group_by(
        RegulatedEntityName,
        DonorName,
        DonorStatus,
        CompanyRegistrationNumber
    ) |>
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
project. In it, create a file called [`config.yaml`](.\config.yaml) and
save the following YAML to it:

``` r
augmenta_config <- "input_csv: data/donations.csv
output_csv: data/donations_classified.csv
model:
  provider: openai
  name: gpt-4o-mini
search:
  engine: brave
  results: 20
# mcpServers:
#   - name: sequential-thinking
#     command: npx
#     args:
#       - \"-y\"
#       - \"@modelcontextprotocol/server-sequential-thinking\"
prompt:
  system: You are an expert researcher whose job is to classify individuals and companies based on their industry.
  user: |
    # Instructions

    Your job is to research \"{{DonorName}}\", a donor to a political party in the UK. Your will determine what industry {{DonorName}} belongs to. The entity could be a company, a trade group, a union, an individual, etc.

    If {{DonorName}} is an individual, you should classify them based on their profession or the industry they are closest associated with. If the documents are about multiple individuals, or if it's not clear which individual the documents refer to, please set the industry to \"Don't know\" and the confidence level to 1. For example, there's no way to know for certain that someone named \"John Smith\" in the documents is the same person as the donor in the Electoral Commission.

    We also know that the donor is a {{DonorStatus}}.

    ## Searching guidelines

    In most cases, you should start by searching for {{DonorName}} without any additional parameters. Where relevant, remove redundant words like \"company\", \"limited\", \"plc\", etc from the search query. If you need to perform another search, try to refine it by adding relevant keywords like \"industry\", \"job\", \"company\", etc. Note that each case will be different, so be flexible and adaptable. Unless necessary, limit your research to two or three searches.

    With each search, select a few sources that are most likely to provide relevant information. Access them using the tools provided. Be critical and use common sense. Use the sequential thinking tool to think about your next steps. ALWAYS cite your sources.

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
  - input: \"Charles A Daniel-Hobbs\"
    output:
      industry: Financial and insurance activities
      explanation: |
        According to [the Wall Street Journal](https://www.wsj.com/market-data/quotes/SFNC/company-people/executive-profile/247375783), Mr. Charles Alexander DANIEL-HOBBS is the Chief Financial Officer and Executive Vice President of Simmons First National Corp, a bank holding company.

        A Charles Alexander DANIEL-HOBBS also operates several companies, such as [DIBDEN PROPERTY LIMITED](https://find-and-update.company-information.service.gov.uk/company/10126637), which Companies House classifies as \"Other letting and operating of own or leased real estate\". However, the information is not clear on whether these are the same person.
      confidence: 2
  - input: \"Unite the Union\"
    output:
      industry: Trade union
      explanation: |
        Unite is [one of the two largest trade unions in the UK](https://en.wikipedia.org/wiki/Unite_the_Union), with over 1.2 million members. It represents various industries, such as construction, manufacturing, transport, logistics and other sectors.
      confidence: 7
  - input: \"Google UK Limited\"
    output:
      industry: Information and communication
      explanation: |
        Google UK Limited is a [subsidiary of Google LLC](https://about.google/intl/ALL_uk/google-in-uk/), a multinational technology company that specializes in Internet-related services and products.

        The company [provides various web based business services](https://www.bloomberg.com/profile/company/1200719Z:LN), including a web based search engine which includes various options such as web, image, directory, and news searches.
      confidence: 10
  - input: \"John Smith\"
    output:
      industry: Don't know
      explanation: |
        The documents about John Smith refer to multiple people (a [British polician](https://en.wikipedia.org/wiki/John_Smith_(Labour_Party_leader)), an [explorer](https://en.wikipedia.org/wiki/John_Smith_(explorer)), a [singer-songwriter](https://johnsmithjohnsmith.com/)), so there's no way to accurately assess what industry this particular individual belongs to.
      confidence: 1
logfire: true"

cat(augmenta_config, file = "config.yaml")
```

A few things to note about the configuration:

- We’re using Brave due to its generous free API tier, but Google search
  results are generally more accurate.
- The industries are based on the [Standard Industrial
  Classification](https://resources.companieshouse.gov.uk/sic/) groups.
  You can probably come up with something more clever.
- We are the “sequential thinking” MCP server to allow the Augmenta to
  reason about its work. This requires you to have Node.js installed.
  You can [read more about how it
  works](https://github.com/Global-Witness/augmenta/blob/main/docs/tools.md)
  or delete the `mcpServers` section if you don’t want to use it.
- We are also using logfire to monitor Augmenta’s progress. This is also
  optional, but it can be useful to see how the model is performing and
  to debug any issues that may arise.

Because we’re using Brave and an OpenAI model, we need API keys for both
services. Save them to a file called `.env` in the root of your project
directory:

    OPENAI_API_KEY=YOUR_KEY_GOES_HERE
    BRAVE_API_KEY=YOUR_KEY_GOES_HERE

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
    select(-DonorStatus, -CompanyRegistrationNumber) |>
    gt() |>
    fmt_markdown(columns = "explanation")
```

    Rows: 5 Columns: 7
    ── Column specification ────────────────────────────────────────────────────────
    Delimiter: ","
    chr (5): RegulatedEntityName, DonorName, DonorStatus, industry, explanation
    dbl (2): CompanyRegistrationNumber, Value

    ℹ Use `spec()` to retrieve the full column specification for this data.
    ℹ Specify the column types or set `show_col_types = FALSE` to quiet this message.

<div id="gwojqxqmth" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>#gwojqxqmth table {
  font-family: system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
&#10;#gwojqxqmth thead, #gwojqxqmth tbody, #gwojqxqmth tfoot, #gwojqxqmth tr, #gwojqxqmth td, #gwojqxqmth th {
  border-style: none;
}
&#10;#gwojqxqmth p {
  margin: 0;
  padding: 0;
}
&#10;#gwojqxqmth .gt_table {
  display: table;
  border-collapse: collapse;
  line-height: normal;
  margin-left: auto;
  margin-right: auto;
  color: #333333;
  font-size: 16px;
  font-weight: normal;
  font-style: normal;
  background-color: #FFFFFF;
  width: auto;
  border-top-style: solid;
  border-top-width: 2px;
  border-top-color: #A8A8A8;
  border-right-style: none;
  border-right-width: 2px;
  border-right-color: #D3D3D3;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #A8A8A8;
  border-left-style: none;
  border-left-width: 2px;
  border-left-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_caption {
  padding-top: 4px;
  padding-bottom: 4px;
}
&#10;#gwojqxqmth .gt_title {
  color: #333333;
  font-size: 125%;
  font-weight: initial;
  padding-top: 4px;
  padding-bottom: 4px;
  padding-left: 5px;
  padding-right: 5px;
  border-bottom-color: #FFFFFF;
  border-bottom-width: 0;
}
&#10;#gwojqxqmth .gt_subtitle {
  color: #333333;
  font-size: 85%;
  font-weight: initial;
  padding-top: 3px;
  padding-bottom: 5px;
  padding-left: 5px;
  padding-right: 5px;
  border-top-color: #FFFFFF;
  border-top-width: 0;
}
&#10;#gwojqxqmth .gt_heading {
  background-color: #FFFFFF;
  text-align: center;
  border-bottom-color: #FFFFFF;
  border-left-style: none;
  border-left-width: 1px;
  border-left-color: #D3D3D3;
  border-right-style: none;
  border-right-width: 1px;
  border-right-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_bottom_border {
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_col_headings {
  border-top-style: solid;
  border-top-width: 2px;
  border-top-color: #D3D3D3;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
  border-left-style: none;
  border-left-width: 1px;
  border-left-color: #D3D3D3;
  border-right-style: none;
  border-right-width: 1px;
  border-right-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_col_heading {
  color: #333333;
  background-color: #FFFFFF;
  font-size: 100%;
  font-weight: normal;
  text-transform: inherit;
  border-left-style: none;
  border-left-width: 1px;
  border-left-color: #D3D3D3;
  border-right-style: none;
  border-right-width: 1px;
  border-right-color: #D3D3D3;
  vertical-align: bottom;
  padding-top: 5px;
  padding-bottom: 6px;
  padding-left: 5px;
  padding-right: 5px;
  overflow-x: hidden;
}
&#10;#gwojqxqmth .gt_column_spanner_outer {
  color: #333333;
  background-color: #FFFFFF;
  font-size: 100%;
  font-weight: normal;
  text-transform: inherit;
  padding-top: 0;
  padding-bottom: 0;
  padding-left: 4px;
  padding-right: 4px;
}
&#10;#gwojqxqmth .gt_column_spanner_outer:first-child {
  padding-left: 0;
}
&#10;#gwojqxqmth .gt_column_spanner_outer:last-child {
  padding-right: 0;
}
&#10;#gwojqxqmth .gt_column_spanner {
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
  vertical-align: bottom;
  padding-top: 5px;
  padding-bottom: 5px;
  overflow-x: hidden;
  display: inline-block;
  width: 100%;
}
&#10;#gwojqxqmth .gt_spanner_row {
  border-bottom-style: hidden;
}
&#10;#gwojqxqmth .gt_group_heading {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  color: #333333;
  background-color: #FFFFFF;
  font-size: 100%;
  font-weight: initial;
  text-transform: inherit;
  border-top-style: solid;
  border-top-width: 2px;
  border-top-color: #D3D3D3;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
  border-left-style: none;
  border-left-width: 1px;
  border-left-color: #D3D3D3;
  border-right-style: none;
  border-right-width: 1px;
  border-right-color: #D3D3D3;
  vertical-align: middle;
  text-align: left;
}
&#10;#gwojqxqmth .gt_empty_group_heading {
  padding: 0.5px;
  color: #333333;
  background-color: #FFFFFF;
  font-size: 100%;
  font-weight: initial;
  border-top-style: solid;
  border-top-width: 2px;
  border-top-color: #D3D3D3;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
  vertical-align: middle;
}
&#10;#gwojqxqmth .gt_from_md > :first-child {
  margin-top: 0;
}
&#10;#gwojqxqmth .gt_from_md > :last-child {
  margin-bottom: 0;
}
&#10;#gwojqxqmth .gt_row {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  margin: 10px;
  border-top-style: solid;
  border-top-width: 1px;
  border-top-color: #D3D3D3;
  border-left-style: none;
  border-left-width: 1px;
  border-left-color: #D3D3D3;
  border-right-style: none;
  border-right-width: 1px;
  border-right-color: #D3D3D3;
  vertical-align: middle;
  overflow-x: hidden;
}
&#10;#gwojqxqmth .gt_stub {
  color: #333333;
  background-color: #FFFFFF;
  font-size: 100%;
  font-weight: initial;
  text-transform: inherit;
  border-right-style: solid;
  border-right-width: 2px;
  border-right-color: #D3D3D3;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#gwojqxqmth .gt_stub_row_group {
  color: #333333;
  background-color: #FFFFFF;
  font-size: 100%;
  font-weight: initial;
  text-transform: inherit;
  border-right-style: solid;
  border-right-width: 2px;
  border-right-color: #D3D3D3;
  padding-left: 5px;
  padding-right: 5px;
  vertical-align: top;
}
&#10;#gwojqxqmth .gt_row_group_first td {
  border-top-width: 2px;
}
&#10;#gwojqxqmth .gt_row_group_first th {
  border-top-width: 2px;
}
&#10;#gwojqxqmth .gt_summary_row {
  color: #333333;
  background-color: #FFFFFF;
  text-transform: inherit;
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#gwojqxqmth .gt_first_summary_row {
  border-top-style: solid;
  border-top-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_first_summary_row.thick {
  border-top-width: 2px;
}
&#10;#gwojqxqmth .gt_last_summary_row {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_grand_summary_row {
  color: #333333;
  background-color: #FFFFFF;
  text-transform: inherit;
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#gwojqxqmth .gt_first_grand_summary_row {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  border-top-style: double;
  border-top-width: 6px;
  border-top-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_last_grand_summary_row_top {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  border-bottom-style: double;
  border-bottom-width: 6px;
  border-bottom-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_striped {
  background-color: rgba(128, 128, 128, 0.05);
}
&#10;#gwojqxqmth .gt_table_body {
  border-top-style: solid;
  border-top-width: 2px;
  border-top-color: #D3D3D3;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_footnotes {
  color: #333333;
  background-color: #FFFFFF;
  border-bottom-style: none;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
  border-left-style: none;
  border-left-width: 2px;
  border-left-color: #D3D3D3;
  border-right-style: none;
  border-right-width: 2px;
  border-right-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_footnote {
  margin: 0px;
  font-size: 90%;
  padding-top: 4px;
  padding-bottom: 4px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#gwojqxqmth .gt_sourcenotes {
  color: #333333;
  background-color: #FFFFFF;
  border-bottom-style: none;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
  border-left-style: none;
  border-left-width: 2px;
  border-left-color: #D3D3D3;
  border-right-style: none;
  border-right-width: 2px;
  border-right-color: #D3D3D3;
}
&#10;#gwojqxqmth .gt_sourcenote {
  font-size: 90%;
  padding-top: 4px;
  padding-bottom: 4px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#gwojqxqmth .gt_left {
  text-align: left;
}
&#10;#gwojqxqmth .gt_center {
  text-align: center;
}
&#10;#gwojqxqmth .gt_right {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
&#10;#gwojqxqmth .gt_font_normal {
  font-weight: normal;
}
&#10;#gwojqxqmth .gt_font_bold {
  font-weight: bold;
}
&#10;#gwojqxqmth .gt_font_italic {
  font-style: italic;
}
&#10;#gwojqxqmth .gt_super {
  font-size: 65%;
}
&#10;#gwojqxqmth .gt_footnote_marks {
  font-size: 75%;
  vertical-align: 0.4em;
  position: initial;
}
&#10;#gwojqxqmth .gt_asterisk {
  font-size: 100%;
  vertical-align: 0;
}
&#10;#gwojqxqmth .gt_indent_1 {
  text-indent: 5px;
}
&#10;#gwojqxqmth .gt_indent_2 {
  text-indent: 10px;
}
&#10;#gwojqxqmth .gt_indent_3 {
  text-indent: 15px;
}
&#10;#gwojqxqmth .gt_indent_4 {
  text-indent: 20px;
}
&#10;#gwojqxqmth .gt_indent_5 {
  text-indent: 25px;
}
&#10;#gwojqxqmth .katex-display {
  display: inline-flex !important;
  margin-bottom: 0.75em !important;
}
&#10;#gwojqxqmth div.Reactable > div.rt-table > div.rt-thead > div.rt-tr.rt-tr-group-header > div.rt-th-group:after {
  height: 0px !important;
}
</style>

| RegulatedEntityName | DonorName | Value | industry | explanation |
|----|----|----|----|----|
| Conservative and Unionist Party | M & M Supplies (UK) PLC | 4166.00 | Wholesale and retail trade; repair of motor vehicles and motorcycles | M & M Supplies (UK) PLC is primarily involved in the wholesale trade, specifically focusing on managing problematic inventory for Fast-Moving Consumer Goods (FMCG) manufacturers. According to their [official website](http://www.mmsupplies.com/), they provide a sales route into the discount channel for manufacturers, which indicates their role in the wholesale distribution of consumer products. The company is classified under the SIC code 46900, which corresponds to non-specialised wholesale trade, further confirming its industry classification. Additionally, they have been operating for over 40 years and serve a large customer base across Europe, indicating a well-established presence in the wholesale market. |
| Liberal Democrats | Cambridge Liberal Democrat Council Group | 1100.00 | Political group | The Cambridge Liberal Democrat Council Group is a political group associated with the Liberal Democrats, a major political party in the UK. They are involved in local governance and represent the Liberal Democrat party within the Cambridge City Council. Their activities include participating in council decisions, advocating for local issues, and campaigning for Liberal Democrat candidates in elections. This classification is supported by information from their official website, which outlines their role in local governance and political activities in Cambridge. You can find more details on their [official site](https://www.cambridgelibdems.org.uk/). |
| Liberal Democrats | Don Harmes dec'd | 3000.00 | Don't know | The search for information on Don Harmes dec’d did not yield specific details about his profession or industry. There were no clear references linking him to a particular field or organization, and the available documents did not provide sufficient context to ascertain his industry affiliation. Therefore, I cannot confidently classify him into a specific industry. |
| SDLP (Social Democratic & Labour Party) | Northern Ireland Assembly | 9326.57 | Public administration and defence; compulsory social security | The Northern Ireland Assembly is the devolved legislature for Northern Ireland, responsible for making laws on a wide range of areas including health, education, and agriculture. It operates under a power-sharing agreement and is a key institution in the governance of Northern Ireland, as established by the Good Friday Agreement. The Assembly’s primary function is to scrutinize the work of ministers and government departments, making it a central body in public administration. More details can be found on the [official Northern Ireland Assembly website](https://www.niassembly.gov.uk/) and its [Wikipedia page](https://en.wikipedia.org/wiki/Northern_Ireland_Assembly). |
| Sinn Féin | House of Commons Department of Resources | 33494.38 | Public administration and defence; compulsory social security | The House of Commons Department of Resources is part of the UK Parliament, which is a key institution in the public administration sector. The House of Commons itself is the lower house of Parliament, responsible for making laws and scrutinizing the government. As a public fund, it operates within the framework of public administration, focusing on governance and legislative functions. The Department of Resources specifically deals with the management of resources within the House of Commons, further emphasizing its role in public administration. For more information, you can refer to the [House of Commons Wikipedia page](https://en.wikipedia.org/wiki/House_of_Commons_of_the_United_Kingdom). |

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
