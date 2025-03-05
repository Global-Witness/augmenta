# Autonomous agent

By default, Augmenta runs in a pre-configured mode where it searches the internet for fixed terms, scrapes a predetrmined number of results, then responds in a predetermined format.

Suppose we're asking Augmenta to determine if "Mitsubishi Research Institute" is a fossil fuel company or not. Augmenta will search for Mitsubishi Research Institute (the exact phrase) and return the first 10 results. Those are extracted and sent as is to the LLM.

This is useful in many cases, but often the search term will not return good or sufficient enough results to produce a good response.

Instead, you can set Augmenta to work autonomously, where it will search for terms that it thinks are relevant, and will continue to search until it is satisfied with the output.

To start, add this to your `config.yml`:

```yaml
agent:
  enabled: true
```

This will enable the agentic mode. In our "Mitsubishi Research Institute", this may look something like this:

- Augmenta will search for "Mitsubishi Research Institute industry"
- From the 20 results, it selects 3 that it thinks are relevant (official website, wikipedia, linkedin)
- Not satisfied, it searches for "Mitsubishi Research Institute fossil fuel ties"
- Extracts 2 more results
- Based on those 5 results, it makes a final decision

This approach is more flexible and should yield better results, particularly in cases where the search term is more ambiguous or the data is not standardised in the original source.

However, it can be slower and more expensive (multiple API calls per classification)

More testing to follow.