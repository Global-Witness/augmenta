# Fixed agent

By default, Augmenta runs in an "autonomous" mode, where it will autonomatically make decisions about what to search for, which resuults to read, and when it has enough information to make a decision.

You may want to switch to a "pre-determined" mode, where you can specify the search terms and the number of results to scrape. This is useful if you want to have more control over the search process, or if you want to use Augmenta in a more deterministic way.

To start, add this to your `config.yml`:

```yaml
agent: fixed
```
