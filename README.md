#### scout (0.1.0)


<img width="2560" height="1440" alt="video demo " src="https://github.com/user-attachments/assets/ca4635ec-4e94-440b-bf56-be73bafe2546" />


#### What it does

Every time you run it, scout finds 5 repositories sifted through a system of filters. It runs a list of searches you configured and scores each repo by how recently it was pushed, how many stars it has, and how well its language and topics match, then prints to your terminal.

The shortlist rotates daily: anything you've already starred is excluded forever, and anything that appeared in the last 7 days is skipped. So you keep seeing fresh repos.


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

#### Tune it for your specialization

Scout ships with defaults tuned for ML, generative AI, game engines, and quant. To make it match your world, edit two files in `~/.scout/`.

`sources.yml` is the list of GitHub searches scout runs. Add, remove, or rewrite entries to point at the topics you actually care about. Anything GitHub's search syntax accepts works here.

`scoring.yml` is where you boost specific languages and topics. Higher numbers (0 to 1) rank a repo higher in the daily top 5.

A few starter recipes you can paste over the defaults:

**Web / frontend dev**
```yaml
preferred_languages:
  TypeScript: 1.0
  JavaScript: 0.9
  Rust: 0.7    # WASM, build tooling
  Go: 0.6      # backends
preferred_topics:
  react: 1.0
  nextjs: 1.0
  svelte: 0.95
  vue: 0.9
  tailwindcss: 0.85
  web-components: 0.8
  vite: 0.8
```

**Systems / backend / infra**
```yaml
preferred_languages:
  Rust: 1.0
  Go: 1.0
  C: 0.9
  C++: 0.9
  Zig: 0.85
preferred_topics:
  kubernetes: 1.0
  observability: 0.95
  distributed-systems: 1.0
  databases: 0.95
  networking: 0.9
  cli: 0.85
  containers: 0.85
```

**Mobile**
```yaml
preferred_languages:
  Swift: 1.0
  Kotlin: 1.0
  Dart: 0.95
  Objective-C: 0.7
preferred_topics:
  ios: 1.0
  android: 1.0
  swiftui: 0.95
  jetpack-compose: 0.95
  flutter: 0.95
  react-native: 0.85
```

**Security / offensive**
```yaml
preferred_languages:
  Python: 1.0
  Go: 0.9
  Rust: 0.85
  C: 0.85
preferred_topics:
  security: 1.0
  pentesting: 1.0
  reverse-engineering: 0.95
  exploit: 0.9
  malware-analysis: 0.9
  fuzzing: 0.85
  cryptography: 0.85
```

You can mix several specializations in one file; the highest matching language and the highest matching topic each contribute to a repo's score. Pair these with matching `queries` in `sources.yml` (e.g. `topic:kubernetes pushed:>{seven_days_ago}`) so the candidate pool actually contains the right repos.

#### Auth (for `scout approve`)

Scout finds a GitHub token in this order:

1. `$GITHUB_TOKEN` or `$GH_TOKEN` env var.
2. `~/.scout/.env` (a `GITHUB_TOKEN=...` line).
3. Whatever `gh auth token` returns, if you have the GitHub CLI installed and logged in.

The easiest path is `gh auth login` once and you're done. The token needs the `public_repo` scope to star. Search-only runs (`scout`, `scout show`) work fine with no token, just at a lower rate limit.

Point scout at a different working dir with `SCOUT_HOME=/some/path scout`.
