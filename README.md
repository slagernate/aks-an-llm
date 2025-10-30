
# aks-an-llm

ask an LLM directly

Some advantages of `aks`:
- Direct query of LLM --prevents model / client from running rampantly in the wrong direction with your codebase
- Fine grain control of files shared (with visibility of tokens shared) (eg don't share massive and/or sensitive files not pertinent to query)
- `response.md` formatting in markdown allows for properly formatted history of answers as well as queries (also in markdown) and responses (no web interfaces vomitting chat bubbles of unformatted plain text).

## Installation
1. Install via pipx locally:
```
cd aks-an-llm
pipx install -e .
```
this will install `aks` symlinnk to: `~/.local/bin/`

2. Add to PATH (if not already; add to ~/.bashrc or ~/.profile to retain updated PATH):
```
export PATH="$HOME/.local/bin:$PATH"
```

3. Test:
```
aks --version
```

4. Make sure you have a [grok API key](https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://console.x.ai/&ved=2ahUKEwjgtebliciQAxW_FDQIHQVPJRwQFnoECBkQAQ&usg=AOvVaw2IAlpnQPMW-m6Yxrrpztsu):
```
export XAI_API_KEY="xai-sOmEkEyHeRe..."
```

or an openai key.

## Usage
```
$ aks --all --query "in this prompt, you can ask a question to an LLM about all of the files (recursively found) in the current directory."
```
The response (along with the query itself) will be appended to `response.md`. Subsequent queries can include `resopnse.md` to give the LLM prior context.

### Model
See help: `--provider` and `--model`

### Query file
Often it is useful to yank a bunch of lines from terminal (e.g. error output) to send to an LLM. You may put them in `query.md`:
```
Summarize this repo
```
After running (optionally excluding some files):
```
aks --all --exclude *.pyc aks.egg.info/ --query-file query.md
```

`response.md` will look like:
```
    ---
    Query Date: 2025-10-28 12:24:45
    Provider: xAI Grok API
    Model: grok-code-fast-1
    Query Source: file: query.md
    Query: Summarize this repo
    ---

    # Repository Summary: aks-an-llm

## Overview
This repository contains a CLI tool named `aks` (intentionally misspelled from "ask") designed to facilitate querying a Large Language Model (LLM) about a codebase. The primary LLM used is Grok, developed by xAI, via their API. The tool is optimized for integration with text editors like Neovim or Vim, especially for handling large codebases with thousands of lines, where web interfaces fall short.

The core functionality involves:
...

## Key Components
...

## Potential Improvements
- Add support for other LLMs or APIs.
...

## Installation
...

## Architecture and Design
...

Overall, this is a lightweight, developer-friendly tool for leveraging AI to analyze and discuss codebases directly from the command line.

```
