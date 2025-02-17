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
library(gt)
```

First, let’s download the data.

``` r
donations_raw <- read_csv("https://search.electoralcommission.org.uk/api/csv/Donations?start={start}&rows=100&query=&sort=AcceptedDate&order=desc&et=pp&date=Accepted&from=2024-07-01&to=2024-09-30&rptPd=&prePoll=false&postPoll=true&register=ni&register=gb&isIrishSourceYes=true&isIrishSourceNo=true&includeOutsideSection75=true")
```

For the purposes of this example, we’ll only keep the columns that
contain information about the donor. We’ll also only look at the first
50 rows to keep things simple.

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

    `summarise()` has grouped output by 'RegulatedEntityName', 'DonorName',
    'DonorStatus'. You can override using the `.groups` argument.

Finally, let’s save this data as a CSV file.

``` r
write_csv(donations, "data/donations.csv")
```

## Augmentation

Now that we have our data, we can use Augmenta to enrich it with
additional information about the donors.

## Setup

First, we need to configure our project. Create a new file called
`config.yaml` and add the following:

``` yaml
input_csv: data/donations.csv
output_csv: data/donations_classified.csv
model:
  name: openai/gpt-4o-mini
  # rate_limit: 1
  max_tokens: 20000
query_col: DonorName
search:
  engine: brave
  results: 10
  rate_limit: 1.5
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
    type: str
    description: Your confidence level in the decision. If you don't have enough information or the documents refer to different organisations that may share a name, please set this to "not confident".
    options:
      - very confident
      - somewhat confident
      - not confident
examples:
  - input: "Charles A Daniel-Hobbs"
    output:
      industry: Financial and insurance activities
      explanation: |
        According to [the Wall Street Journal](https://www.wsj.com/market-data/quotes/SFNC/company-people/executive-profile/247375783), Mr. Charles Alexander DANIEL-HOBBS is the Chief Financial Officer and Executive Vice President of Simmons First National Corp, a bank holding company.
        
        A Charles Alexander DANIEL-HOBBS also operates several companies, such as [DIBDEN PROPERTY LIMITED](https://find-and-update.company-information.service.gov.uk/company/10126637), which Companies House classifies as "Other letting and operating of own or leased real estate". However, the information is not clear on whether these are the same person.
      confidence: somewhat confident
  - input: "Unite the Union"
    output:
      industry: Trade union
      explanation: |
        Unite is [one of the two largest trade unions in the UK](https://en.wikipedia.org/wiki/Unite_the_Union), with over 1.2 million members. It represents various industries, such as construction, manufacturing, transport, logistics and other sectors.
      confidence: very confident
  - input: "Google UK Limited"
    output:
      industry: Information and communication
      explanation: |
        Google UK Limited is a [subsidiary of Google LLC](https://about.google/intl/ALL_uk/google-in-uk/), a multinational technology company that specializes in Internet-related services and products.

        The company [provides various web based business services](https://www.bloomberg.com/profile/company/1200719Z:LN), including a web based search engine which includes various options such as web, image, directory, and news searches. 
      confidence: very confident
```

A few things to note about this configuration:

- We’re using Brave due to its generous free API tier, but Google will
  probably work better.
- Because our dataset is US-centric, we’re setting the country to “GB”
  in Brave. This should help to filter some of the irrelevant results.
- The industries are based on the [Standard Industrial
  Classification](https://resources.companieshouse.gov.uk/sic/) groups.
  You can probably come up with something more clever.

Because we want to use Brave and GPT-4o-mini, we need access keys for
both services. Save them to a file called `.env`:

    BRAVE_API_KEY=YOUR_KEY_GOES_HERE
    OPENAI_API_KEY=YOUR_KEY_GOES_HERE

## Running the augmentation

Make sure you have `augmenta`
[installed](https://github.com/Global-Witness/augmenta/?tab=readme-ov-file#installation),
open the terminal and navigate to the directory where you saved the
data, configuration file and API keys.

Run the following command to start the classification.

``` bash
augmenta config.yaml
```

This should take a few minutes. Once it’s done, you should see a new
file called `data/donations_classified.csv` with the augmented data.

``` r
read_csv("data/donations_classified.csv") |>
  select(-DonorStatus, -CompanyRegistrationNumber) |>
  gt() |>
  fmt_markdown(columns = c(explanation))
```

    Rows: 9 Columns: 8
    ── Column specification ────────────────────────────────────────────────────────
    Delimiter: ","
    chr (6): RegulatedEntityName, DonorName, DonorStatus, industry, explanation,...
    dbl (2): CompanyRegistrationNumber, Value

    ℹ Use `spec()` to retrieve the full column specification for this data.
    ℹ Specify the column types or set `show_col_types = FALSE` to quiet this message.

<div id="nqqnotdqwb" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>#nqqnotdqwb table {
  font-family: system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
&#10;#nqqnotdqwb thead, #nqqnotdqwb tbody, #nqqnotdqwb tfoot, #nqqnotdqwb tr, #nqqnotdqwb td, #nqqnotdqwb th {
  border-style: none;
}
&#10;#nqqnotdqwb p {
  margin: 0;
  padding: 0;
}
&#10;#nqqnotdqwb .gt_table {
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
&#10;#nqqnotdqwb .gt_caption {
  padding-top: 4px;
  padding-bottom: 4px;
}
&#10;#nqqnotdqwb .gt_title {
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
&#10;#nqqnotdqwb .gt_subtitle {
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
&#10;#nqqnotdqwb .gt_heading {
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
&#10;#nqqnotdqwb .gt_bottom_border {
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
}
&#10;#nqqnotdqwb .gt_col_headings {
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
&#10;#nqqnotdqwb .gt_col_heading {
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
&#10;#nqqnotdqwb .gt_column_spanner_outer {
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
&#10;#nqqnotdqwb .gt_column_spanner_outer:first-child {
  padding-left: 0;
}
&#10;#nqqnotdqwb .gt_column_spanner_outer:last-child {
  padding-right: 0;
}
&#10;#nqqnotdqwb .gt_column_spanner {
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
&#10;#nqqnotdqwb .gt_spanner_row {
  border-bottom-style: hidden;
}
&#10;#nqqnotdqwb .gt_group_heading {
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
&#10;#nqqnotdqwb .gt_empty_group_heading {
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
&#10;#nqqnotdqwb .gt_from_md > :first-child {
  margin-top: 0;
}
&#10;#nqqnotdqwb .gt_from_md > :last-child {
  margin-bottom: 0;
}
&#10;#nqqnotdqwb .gt_row {
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
&#10;#nqqnotdqwb .gt_stub {
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
&#10;#nqqnotdqwb .gt_stub_row_group {
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
&#10;#nqqnotdqwb .gt_row_group_first td {
  border-top-width: 2px;
}
&#10;#nqqnotdqwb .gt_row_group_first th {
  border-top-width: 2px;
}
&#10;#nqqnotdqwb .gt_summary_row {
  color: #333333;
  background-color: #FFFFFF;
  text-transform: inherit;
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#nqqnotdqwb .gt_first_summary_row {
  border-top-style: solid;
  border-top-color: #D3D3D3;
}
&#10;#nqqnotdqwb .gt_first_summary_row.thick {
  border-top-width: 2px;
}
&#10;#nqqnotdqwb .gt_last_summary_row {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
}
&#10;#nqqnotdqwb .gt_grand_summary_row {
  color: #333333;
  background-color: #FFFFFF;
  text-transform: inherit;
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#nqqnotdqwb .gt_first_grand_summary_row {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  border-top-style: double;
  border-top-width: 6px;
  border-top-color: #D3D3D3;
}
&#10;#nqqnotdqwb .gt_last_grand_summary_row_top {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-left: 5px;
  padding-right: 5px;
  border-bottom-style: double;
  border-bottom-width: 6px;
  border-bottom-color: #D3D3D3;
}
&#10;#nqqnotdqwb .gt_striped {
  background-color: rgba(128, 128, 128, 0.05);
}
&#10;#nqqnotdqwb .gt_table_body {
  border-top-style: solid;
  border-top-width: 2px;
  border-top-color: #D3D3D3;
  border-bottom-style: solid;
  border-bottom-width: 2px;
  border-bottom-color: #D3D3D3;
}
&#10;#nqqnotdqwb .gt_footnotes {
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
&#10;#nqqnotdqwb .gt_footnote {
  margin: 0px;
  font-size: 90%;
  padding-top: 4px;
  padding-bottom: 4px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#nqqnotdqwb .gt_sourcenotes {
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
&#10;#nqqnotdqwb .gt_sourcenote {
  font-size: 90%;
  padding-top: 4px;
  padding-bottom: 4px;
  padding-left: 5px;
  padding-right: 5px;
}
&#10;#nqqnotdqwb .gt_left {
  text-align: left;
}
&#10;#nqqnotdqwb .gt_center {
  text-align: center;
}
&#10;#nqqnotdqwb .gt_right {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
&#10;#nqqnotdqwb .gt_font_normal {
  font-weight: normal;
}
&#10;#nqqnotdqwb .gt_font_bold {
  font-weight: bold;
}
&#10;#nqqnotdqwb .gt_font_italic {
  font-style: italic;
}
&#10;#nqqnotdqwb .gt_super {
  font-size: 65%;
}
&#10;#nqqnotdqwb .gt_footnote_marks {
  font-size: 75%;
  vertical-align: 0.4em;
  position: initial;
}
&#10;#nqqnotdqwb .gt_asterisk {
  font-size: 100%;
  vertical-align: 0;
}
&#10;#nqqnotdqwb .gt_indent_1 {
  text-indent: 5px;
}
&#10;#nqqnotdqwb .gt_indent_2 {
  text-indent: 10px;
}
&#10;#nqqnotdqwb .gt_indent_3 {
  text-indent: 15px;
}
&#10;#nqqnotdqwb .gt_indent_4 {
  text-indent: 20px;
}
&#10;#nqqnotdqwb .gt_indent_5 {
  text-indent: 25px;
}
&#10;#nqqnotdqwb .katex-display {
  display: inline-flex !important;
  margin-bottom: 0.75em !important;
}
&#10;#nqqnotdqwb div.Reactable > div.rt-table > div.rt-thead > div.rt-tr.rt-tr-group-header > div.rt-th-group:after {
  height: 0px !important;
}
</style>

| RegulatedEntityName | DonorName | Value | industry | explanation | confidence |
|----|----|----|----|----|----|
| Labour Party | Labour Together Limited | 53824.20 | NGO or think-tank | Labour Together Limited is a British think tank closely associated with the Labour Party. Founded in June 2015, it has played a significant role in shaping political policy and public opinion regarding Labour Party strategies. The organization has hybrid functions, including policy analysis, advocacy for Labour’s political agenda, and efforts to unify various factions within the party, making it comparable to other influential think tanks in the UK political landscape. Its recent activities include publishing reports on political strategies and engaging in electoral assessments, highlighting its role in policy debates and promoting Labour’s electoral success. More details can be found on their official site <a href="https://www.labourtogether.uk/">Labour Together</a>. | very confident |
| Labour Party | The Good Faith Partnership LLP | 15660.00 | Professional, scientific and technical activities | The Good Faith Partnership LLP operates as a social consultancy, addressing complex societal challenges through collaboration among various sectors including government, businesses, charities, and faith-based organizations. Their focus on public policy, public affairs, and strategic initiatives aligns closely with the Professional, scientific and technical activities industry. Moreover, they position themselves as a bridge connecting political, civil society, and faith sectors to foster common initiatives and solutions, indicating a strong engagement within the realm of professional consultancy services. For more information on their work, you can visit their <a href="https://goodfaith.org.uk/">website</a>. | very confident |
| Liberal Democrats | JOHN HEMMING TRADING LIMITED | 1000.00 | Arts, entertainment and recreation | According to the documents, JOHN HEMMING TRADING LIMITED has a registered business nature of ‘Operation of arts facilities’ (SIC Code 90040). This categorically places the company within the arts and entertainment sector, focusing on facilities that likely host events such as performances, exhibitions, or other art-related activities. The company has been active since its incorporation on 3 August 2011 and is based in Birmingham, West Midlands. Additionally, other documents related to John Hemming, the owner of this company, hint at a diverse background including membership in arts-related unions, but the primary classification remains in the arts industry. | very confident |
| Liberal Democrats | Patricia Bell | 2790.00 | Education | Patricia Bell is a prominent figure in the field of women’s studies and black feminism, serving as a professor emerita at the University of Georgia. Her extensive background includes being a co-founder of the National Women’s Studies Association and contributing to various educational programs and journals related to women’s issues. She has authored multiple influential books that have been recognized in the academic community, such as <em>The Firebrand and the First Lady</em>, which relate to social justice and women’s studies. Her position in academia and her contributions to education and scholarship clearly align her with the ‘Education’ industry. | very confident |
| Liberal Democrats | Robert H Miall | 2500.00 | Arts, entertainment and recreation | Robert H Miall is primarily known as a writer, with notable works including titles related to science fiction such as ‘UFO-1: The Flesh Hunters’ and ‘The Protectors.’ According to sources, including <a href="https://www.goodreads.com/author/show/1235956.Robert_Miall">Goodreads</a>, he was active in publishing through the 1970s and has a body of work that includes several books. His profession and contributions align closely with the Arts and Entertainment sector, specifically literature and recreation activities. | very confident |
| Liberal Democrats | Scottish Parliament. | 4376.10 | Public administration and defence; compulsory social security | The Scottish Parliament is the unicameral legislature responsible for representing the citizens of Scotland and for making laws affecting various areas within Scotland’s legislative competence. It was established following a referendum in 1997 and has the power to legislate on numerous devolved issues as defined by the Scotland Act 1998. The Parliament operates within the framework of the UK’s political structure and holds significant roles in public governance, making it part of the public administration industry. You can find more detailed information on its functions and legislative powers at the official <a href="https://www.parliament.scot/">Scottish Parliament website</a>. | very confident |
| Liberal Democrats | Stephen F Gosling | 2500.00 | Arts, entertainment and recreation | Stephen F. Gosling is identified as a professional pianist, well-known for his performances in the contemporary music scene across various regions, including the U.S. and Europe. His significant contributions include performances with well-respected ensembles and orchestras, highlighting his role as a musical artist. Notably, he has received acclaim in reviews from sources like The New York Times and Washington Post, which emphasize his artistic skills and contributions to music. Additionally, the various performances and collaborations he is involved in falls under the arts industry. This classification aligns with his engagement and reputation in the contemporary music scene, making it clear that he is tied to the ‘Arts, entertainment and recreation’ industry. Here’s more on his background: <a href="https://www.newyorker.com/goings-on-about-town/classical-music/stephen-gosling">New Yorker</a> describes his strength and appeal as a pianist. | very confident |
| Liberal Democrats | Wirral Liberal Club | 127709.80 | Accommodation and food service activities | The Wirral Liberal Club was previously classified as a pub and operated under a full pub license. Despite its closure in April 2019, it held a license and was involved in hospitality services, which places it under the accommodation and food service activities industry. According to <a href="https://www1.camra.org.uk/pubs/wirral-liberal-club-oxton-132116">CAMRA</a>, the club is located in a converted house and operated as a pub until its closure. While it is not currently operational, its historical function aligns with this classification. | very confident |
| Ulster Unionist Party | Northern Ireland Assembly | 7069.03 | Public administration and defence; compulsory social security | The Northern Ireland Assembly is a devolved legislature responsible for making laws on various local matters including housing, health, education, and agriculture, among others. It is the official body for governance in Northern Ireland, created as part of the Good Friday Agreement to facilitate power-sharing between different political groups. As a legislative body, it is primarily associated with public administration and governance rather than any specific traditional industry. This classification aligns with the Assembly’s role in overseeing government departments and granting democratic representation to the Northern Irish public. For more details, you can visit the official website of the <a href="https://www.niassembly.gov.uk/">Northern Ireland Assembly</a> for further insights into its duties and operations. | very confident |

</div>
