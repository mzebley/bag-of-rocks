# Privacy policy

Last updated: 2026-11-02. Applies to the Bag of Rocks skill and plugin by Mark Zebley.

**Bag of Rocks collects, stores, and sends no data to its author or to any third party.** It has no servers, accounts, telemetry, analytics, or tracking.

## What the skill does with data

- **Instructions only.** The skill is a set of instructions plus two Python helpers (`build_packet.py`, `trace_to_run.py`) and an HTML report template. The helpers read and write files on your machine and make no network requests.
- **Your agent does the browsing.** Your AI agent, not this skill, opens the URLs you give it, takes screenshots, and types into pages. What it sends to its model provider is governed by that provider's terms and your agent's settings.
- **Run files stay local.** Run folders (packets, traces, screenshots, reports) are written where you or your agent choose, usually `.bag-of-rocks/runs/` in your project. Delete them whenever you like.
- **Report verdicts stay in your browser.** Calibration filmstrips save reviewer verdicts in the browser's local storage on your machine. Exported verdicts are files you download.
- **Credentials stay out of files.** The skill tells the agent never to write credentials into packets, traces, or reports, and keeps account details as aliases.

## Data categories, purposes, recipients, and retention

| | |
| --- | --- |
| Personal data collected by the author | None |
| Recipients | None. Data you give your agent goes only to the services you and your agent use. |
| Retention | Local files remain until you delete them. Nothing is retained by the author. |
| Children | Not directed at people under 18. |

## Your controls

Uninstall the plugin or delete the skill folder to remove it. Delete run folders to remove their screenshots and traces. Clear your browser's site data to remove saved verdicts.

## Contact

Questions or concerns: open an issue at https://github.com/mzebley/bag-of-rocks/issues.
