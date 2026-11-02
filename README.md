# Bag of Rocks

Give an agent a goal without showing it the route. Watch where it gets stuck, then review an annotated timeline of what happened.

Bag of Rocks runs a blind, synthetic UX walkthrough of a rendered app. A tester persona works through your screens as someone unfamiliar with the product, nervous about mistakes, and unsure around technology. A coordinator keeps the intended path hidden from the tester, then compares the tester's recorded actions with it. You get an annotated screenshot filmstrip, findings linked to evidence, and saved findings called "rocks" for later regression checks.

The findings are hypotheses to investigate. They don't measure real users, predict how many would fail, or replace an accessibility audit.

## Use it

Ask Claude for a UX walkthrough, or run `/bag-of-rocks`:

```text
Use bag-of-rocks.
Goal: Change my mailing address to 12 Elm St.
Start: https://staging.example.test/
Mutations: none
```

Point it at a staging or local site you're authorized to test. With `Mutations: none`, the tester stops before saving anything and records what it would have done.

## What it runs and sends

- **Runs:** the skill's instructions, two local Python helpers that only read and write files, and a static HTML report. No network requests.
- **Browses:** your agent's own browser tool opens the URLs you give it. The plugin adds no browser, server, or MCP connection.
- **Sends:** nothing to the author or any third party. No accounts, telemetry, or analytics.
- **Stores:** run folders where you choose, and calibration verdicts in your browser's local storage.

See [PRIVACY.md](PRIVACY.md).

## Requirements

An agent with screenshot-based browser control and file access, and Python 3 for the helpers. Fresh subagents for the tester give the strongest blinding.

## More

Source, changelog, calibration fixtures, and documentation: https://github.com/mzebley/bag-of-rocks. MIT license.
