import json
import re
import argparse

def purify_code_from_jsonl(input_file, output_file, purify_field="code_after", purify_fields=None, keep_language_mark=False):
    """
    Extract code from markdown code blocks in a JSONL file and write the purified code to an output file.

    Args:
        input_file (str): Path to the input JSONL file containing code snippets.
        output_file (str): Path to the output file for purified code.
        purify_field (str): JSON field containing the code snippet. Defaults to "code_after". 
            If purify_fields is not None, this will be ignored.
        purify_fields (list): JSONL field(s) containing the code snippet. Defaults to None. 
        keep_language_mark (bool): If True, retains the language marker as a comment. Defaults to False.

    Raises:
        ValueError: If no code block or end marker is found.
    """
    # Pattern to match ```lang\n<code>``` blocks
    pattern = re.compile(r'```(?P<lang>[^\s`]+)?\s*\n(?P<code>[\s\S]*?)```', re.MULTILINE)

    # If purify_fields is not provided, use purify_field as the only field
    if purify_fields is None:
        purify_fields = [purify_field]

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            data = json.loads(line)
            out_data = data.copy()
            for field in purify_fields:
                if field in data:
                    snippet = data[field]
                    try:
                        matches = list(pattern.finditer(snippet))
                        if not matches:
                            raise ValueError('No code block found')

                        # Select first non-markdown block if present, else first match
                        selected = None
                        for m in matches:
                            lang = (m.group('lang') or '').lower()
                            if lang != 'markdown':
                                selected = m
                                break
                        if not selected:
                            selected = matches[0]  # Fallback to first match, i.e. "markdown"

                        lang = selected.group('lang') or ''
                        code = selected.group('code').strip()

                        # 如果提取的 code 内容为空，抛出异常
                        if not code:
                            raise ValueError('Extracted code block is empty')
                        
                        if code.startswith("python"):
                            code = "\n".join(code.split("\n")[1:])
                            lang = "python"

                        # Optionally retain language marker as comment
                        if keep_language_mark and lang:
                            code = f"## {lang}\n" + code

                        out_data[f'{field}_purify'] = code
                    except Exception as e:
                        print(f"Failed to process line: {line.strip()}\nError: {e}")

            outfile.write(json.dumps(out_data, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Purify code from JSONL file.")
    parser.add_argument("input_file", type=str, help="Path to the input JSONL file.")
    parser.add_argument("output_file", type=str, help="Path to the output JSONL file.")
    parser.add_argument("--purify_field", type=str, default="code_after", help="Field containing the code snippet. Default is 'code_after'.")
    parser.add_argument("--keep_language_mark", action="store_true", help="Retain the language marker as a comment.")

    args = parser.parse_args()

    purify_code_from_jsonl(
        input_file=args.input_file,
        output_file=args.output_file,
        purify_field=args.purify_field,
        keep_language_mark=args.keep_language_mark
    )