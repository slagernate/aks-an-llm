#!/usr/bin/env python3
import os
import tempfile
import glob
import sys
import argparse
import threading
import time
import fnmatch
from openai import OpenAI
from datetime import datetime

__version__ = "1.0.0"

def show_version():
    print(f"Ask LLM Tool v{__version__}")
    sys.exit(0)

def show_help():
    print("""
Ask LLM Tool - Share Codebase with LLM Tool
Usage:
    aks [FILES...] [--query QUERY | --query-file FILE | --query-history [LINES]] [--exclude EXCLUDE...] [--all]
    aks -h, --help
    aks -v, --version
Arguments:
    FILES Specific files or glob patterns to include (e.g., *.py, src/**/*.cpp, "*"; optional; defaults to all .cpp, .hpp, .py recursively)
Options:
    --query, -q QUERY Your query about the codebase (optional)
    --query-file, -f FILE Read query from file (mutually exclusive with --query and --query-history)
    --query-history, -H [LINES] Read last LINES (default 100) from ~/.bash_history as query (mutually exclusive with --query and --query-file)
    --exclude, -x EXCLUDE... Glob patterns to exclude (e.g., --exclude poetry.lock tests/*; repeatable)
    --all Include all files recursively (equivalent to "**/*"; overrides FILES)
    -h, --help Show this help message
    -v, --version Show version info
Environment:
    Set XAI_API_KEY to your xAI API key[](https://console.x.ai/)
    """)
    sys.exit(0)

def pretty_number(n):
   """Format large numbers in engineering style (e.g., 516930 -> '517k')."""
   if n < 1000:
       return str(n)
   elif n < 1000000:
       return f"{round(n / 1000)}k"
   else:
       return f"{round(n / 1000000)}M"  # In case of very large numbers

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(add_help=False) # Disable default help
    parser.add_argument('files', nargs='*', help='Specific files or glob patterns to include')
    parser.add_argument('--query', '-q', help='Query string')
    parser.add_argument('--query-file', '-f', help='File containing query string')
    parser.add_argument('--exclude', '-x', action='append', default=[], help='Glob pattern to exclude')
    parser.add_argument('--all', action='store_true', help='Include all files recursively')
    parser.add_argument('--provider', choices=['xai', 'openai', 'ollama'], default='xai', help='LLM provider (default: xai)')
    parser.add_argument('--model', default='grok-code-fast-1', help='LLM model name')
    parser.add_argument('-h', '--help', action='store_true', help='Show help')
    parser.add_argument('-v', '--version', action='store_true', help='Show version')
    args = parser.parse_args()
    if args.version:
        show_version()
    if args.help:
        show_help()

    # Validate mutually exclusive query options
    query_methods = sum([bool(args.query), bool(args.query_file)])
    if query_methods > 1:
        print("Error: --query, --query-file, and are mutually exclusive.", file=sys.stderr)
        sys.exit(1)
    # If --all is used and positional files are provided, treat them as additional excludes
    if args.all and args.files:
        args.exclude.extend(args.files)

    # Step 1: Determine files (specific/globbed or default globs)
    if args.all:
        all_files = glob.glob('**/*', recursive=True)
        all_files = [f for f in all_files if os.path.isfile(f)]
        print(f"Using {len(all_files)} all files recursively (--all flag)")
    elif args.files:
        all_files = []
        for pattern in args.files:
            # Auto-adjust simple top-level globs to recursive
            if pattern.startswith('*') and '**' not in pattern:
                pattern = '**/*' + pattern[1:]
            expanded = glob.glob(pattern, recursive=True)
            all_files.extend(expanded)
        all_files = [f for f in all_files if os.path.isfile(f)]
        print(f"Using {len(all_files)} expanded files from patterns: {args.files}")
    else:
        cpp_files = glob.glob('**/*.cpp', recursive=True)
        hpp_files = glob.glob('**/*.hpp', recursive=True) + glob.glob('**/*.h', recursive=True)
        py_files = glob.glob('**/*.py', recursive=True)
        all_files = cpp_files + hpp_files + py_files
        print(f"Found {len(all_files)} files via default glob: {len(cpp_files)} .cpp, {len(hpp_files)} .h[pp], {len(py_files)} .py")
    # Apply exclusions
    if args.exclude:
        initial_count = len(all_files)
        all_files = [f for f in all_files if not any(fnmatch.fnmatch(f, excl) for excl in args.exclude)]
        excluded_count = initial_count - len(all_files)
        print(f"Excluded {excluded_count} files matching patterns: {args.exclude}")
    if not all_files:
        print("No files found after exclusions.")
        sys.exit(1)

    # Step 1.5: Read and store file contents for token calculation
    file_contents = {}
    total_chars = 0
    print(f"Files included ({len(all_files)} total):")
    for file_path in all_files:
        try:
            rel_path = os.path.relpath(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_contents[file_path] = content
            chars = len(content)
            tokens = chars // 4
            total_chars += chars
            print(f" - {rel_path}: {pretty_number(chars)} chars (~{pretty_number(tokens)} tokens)")
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
    if not file_contents:
        print("No readable files found.")
        sys.exit(1)
    # Step 2: Concatenate contents into a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        for file_path, content in file_contents.items():
            rel_path = os.path.relpath(file_path)
            tmp_file.write(f"\n--- {rel_path} ---\n")
            tmp_file.write(content)
        temp_path = tmp_file.name
    # Read the temp file content
    with open(temp_path, 'r', encoding='utf-8') as f:
        codebase_content = f.read()
    os.unlink(temp_path) # Clean up temp file

    # Step 3: Get user query from command line, file, history, or input
    query_source = "interactive input"
    if args.query_file is not None:
        try:
            with open(args.query_file, 'r', encoding='utf-8') as f:
                user_query = f.read().strip()
            query_source = f"file: {args.query_file}"
        except Exception as e:
            print(f"Error reading query file {args.query_file}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.query:
        user_query = args.query.strip()
        query_source = "command-line argument"
    else:
        user_query = input("Enter your query about the codebase: ").strip()
        query_source = "interactive input"
    if not user_query:
        print("No query provided.")
        sys.exit(1)
    print(f"User query source: {query_source}")

    # Step 4: Estimate tokens and prompt if >2000 (rough approx: chars / 4)
    full_prompt = f'Here is the content of my codebase files:\n\n{codebase_content}\n\nQuery: {user_query}'
    num_chars = len(full_prompt)
    approx_tokens = num_chars // 4
    print(f"Full prompt length: {pretty_number(num_chars)} chars (~{pretty_number(approx_tokens)} tokens)")
    model_context_limit = 256000  # grok-code-fast-1 context window
    if approx_tokens > model_context_limit:
        print(f"Warning: Input prompt approx. {approx_tokens} tokens exceeds model context limit ({model_context_limit}). Proceed anyway? (y/n): ", end='')
        if input().strip().lower() != 'y':
            print("Aborted.")
            sys.exit(1)
    # Step 5: Set up xAI Grok API client (requires XAI_API_KEY env var set to your xAI API key)
    # Get your API key from https://console.x.ai/
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("Error: Set XAI_API_KEY environment variable with your xAI API key.", file=sys.stderr)
        print("Visit https://x.ai/api for details.", file=sys.stderr)
        sys.exit(1)


    if args.provider == 'xai':
        client = OpenAI(api_key=os.getenv('XAI_API_KEY'), base_url='https://api.x.ai/v1')
    elif args.provider == 'openai':
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))  # Set this env var

    # Spinner function for waiting animation
    def spinner(stop_event, start_time):
        spinner_chars = '|/-\\'
        i = 0
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            sys.stdout.write(f'\rWaiting for Grok... {spinner_chars[i % len(spinner_chars)]} ({elapsed:.1f}s)')
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * 50 + '\r') # Clear the spinner line
        sys.stdout.flush()

    # Step 6: Send to Grok API with spinner
    print("Preparing API request...")
    stop_event = threading.Event()
    start_time = time.time()
    spinner_thread = threading.Thread(target=spinner, args=(stop_event, start_time))
    spinner_thread.start()

    try:
        response = client.chat.completions.create(
            model=args.model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are Grok, a helpful AI built by xAI. Analyze the provided codebase and respond to the user query.'
                },
                {
                    'role': 'user',
                    'content': full_prompt
                }
            ],
            max_tokens=2000, # Adjust as needed
            temperature=0.7,
            stream=False
        )
        stop_event.set()
        spinner_thread.join()
        response_content = response.choices[0].message.content
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = f"""
---
Query Date: {current_date}
Provider: xAI Grok API
Model: grok-code-fast-1
Query Source: {query_source}
---
Query Start
---
{user_query}

---
Query End
---

"""
        with open('response.md', 'a', encoding='utf-8') as f:
            f.write(metadata + response_content + "\n\n---\n\n")
        print(f"Response appended to response.md")
    except Exception as e:
        print("API call failed")
        stop_event.set()
        spinner_thread.join()
        print(f"\nError calling API: {e}", file=sys.stderr)
        print("Ensure you have the 'openai' package: pip install openai", file=sys.stderr)
        print("For more API details: https://x.ai/api", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
