
# aks-an-llm

Query / aks \[sic\] an LLM with fine grain control over context / files in your repo / directory.

Primarily used with neovim / vim; `aks` is much faster / better when dealing with thousands of lines of code (the web interface is just not cut out for this).

## Installation
1. Install via pipx locall:
```
cd aks-an-llm
pipx install -e .
```
this will install: `~/.local/bin/aks`

2. Add to PATH (if not already; add to ~/.bashrc or ~/.profile to retain updated PATH):
```
export PATH="$HOME/.local/bin:$PATH"
```

3. Test:
```
which aks
```
should print
```
/home/$YOUR_USER_NAME/.local/bin/aks
```

4. Make sure you have a grok API key:
```
export XAI_API_KEY="xai-sOmEkEyHeRe..."
```

## Usage
```
$ aks --all --query "in this prompt, you can ask a question to an LLM about all of the files (recursively found) in the current directory."
```
The response (along with the query itself) will be appended to `response.md`. Subsequent queries can include `resopnse.md` to give the LLM prior context.

Often it is useful to yank a bunch of lines from terminal (e.g. error output) to send to an LLM. You may put them in `query.md`:
```
Summarize this repo
```
After running (optionally excluding some files):
```
aks --all --exclude *.pyc --query-file query.md
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
