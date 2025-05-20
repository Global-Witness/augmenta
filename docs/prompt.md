# Writing good prompts

A well-written prompt will dramatically increase the quality of your results.

There are several guides for how to write prompts you should look at:
- [Anthropic: Prompt engineering overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [OpenAI: Prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering)

On this page, we'll focus on a few tips and tricks that will help you get better results from Augmenta.

### Test and iterate

Start with a small sample of the data you want to augment, something like 20-50 rows. You will likely need to iterate on your prompt several times to get the results you want, and this will be much faster (and cheaper) with a smaller dataset.

### Be descriptive

Large Language Models can be easily swayed by the information they find. For example, if you ask whether an energy company is a fossil fuel company, the AI may say it isn't because the company has pledged to go carbon neutral by 2030.

You can avoid this by being as descriptive as possible with your prompt. Include something like this in the prompt: "Please be critical and objective about the involvement of {{company_name}} in the exploration, extraction, refining, trading, specialized transportation of oil, gas, coal, or blue hydrogen, or sale of electricity derived from them. Please do not consider any pledges or commitments to go carbon neutral or reduce emissions."

The more descriptive and specific your language is, the better your results will be. Don't be afraid to reapeat yourself, and feel free to WRITE IN ALL CAPS for keywords or phrases you want to emphasise.

### Provide examples

You can use Augmenta by just writing a well-written prompt, and you're likely going to get decent results. This is called "zero-shot" prompting.

However, the quality of the results can dramatically increase if you provide a few examples of the output you're looking for. This is called "few-shot" prompting.

The examples in your YAML should mirror the `structure` you've defined.

```yaml
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

Ideally, pick some examples from your dataset that are representative of the kind of data you're working with.

Try to provide at least 3-5 examples, particularly focusing on edge cases or ambiguous examples. For example, the AI might classify a car manufacturer as a fossil fuel company, but if your definition doesn't include that industry, an example will help the AI understand that.

Avoid negative examples. Like humans, LLMs have a "[pink elephant](https://arxiv.org/html/2404.15154v1)" problem: if you tell them not to think of a pink elephant, they'll think of a pink elephant.

## Leave room for ambiguity

There will be many cases where the AI won't be able to confidently produce the data you want. Rather than forcing it into a response it might [hallucinate](https://en.wikipedia.org/wiki/Hallucination_(artificial_intelligence)), you should offer a way for the AI to say "I don't know".

## Use chain-of-thoguht

[Chain-of-thought](https://www.promptingguide.ai/techniques/cot) is a technique that allows LLMs to reason before responding. It can improve the quality of the output by ~10%.

You can use this technique with Augmenta like this:

```yaml
structure:
  chain_of_thought:
    type: str
    description: Understand the task and make a complete plan to accomplish it. Explain your reasoning. Then, carry out the plan, think of potential issues that might come up, then show your answer. Assess your own answer, think of ways to improve it, and then show the improved answer.
  answer:
    type: str
    description: What is the answer to the question?
```

Adapt the text for your specific use case.

You may also add a "[sequential thinking](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)" [MCP tool](/docs/tools.md) to your project by adding the following to your YAML configuration:

```yaml
mcpServers:
  - name: sequential-thinking
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-sequential-thinking"
```