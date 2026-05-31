# scout

#### What it does

Every time you run it, scout asks GitHub "what are the top 5 repos I should be looking at right now?" It runs a list of searches you configured (deep learning, generative AI, game engines, quant trading, whatever you care about), scores each repo by how recently it was pushed, how many stars it has, and how well its language and topics match your tastes, then prints the top 5 to your terminal.

Every run is also saved to `~/.scout/reports/YYYY-MM-DD.md` so you can flip back to old picks. Run `scout approve` to walk the shortlist and star the ones you like with one keystroke each.

It's a daily 30-second habit. No web UI, no account, no LLM, no nonsense.

#### Install

```
pipx install git+https://github.com/alexph10/github-curate
```

`scout` is now on your PATH.

#### Use

```
scout              build today's shortlist and print it
scout show         reprint the latest report
scout list         list every report you've ever generated
scout approve .    walk today's picks and star the good ones
scout --help       everything else
```

The first run creates `~/.scout/` and drops two editable config files in it: `sources.yml` (what to search for) and `scoring.yml` (how to weight results). Edit them however you like.

#### Auth (for `scout approve`)

Scout finds a GitHub token in this order:

1. `$GITHUB_TOKEN` or `$GH_TOKEN` env var.
2. `~/.scout/.env` (a `GITHUB_TOKEN=...` line).
3. Whatever `gh auth token` returns, if you have the GitHub CLI installed and logged in.

The easiest path is `gh auth login` once and you're done. The token needs the `public_repo` scope to star. Search-only runs (`scout`, `scout show`) work fine with no token, just at a lower rate limit.

Point scout at a different working dir with `SCOUT_HOME=/some/path scout`.
