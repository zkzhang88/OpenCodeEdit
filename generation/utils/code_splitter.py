from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
import re

def split_identifier(identifier):
    """
    Splits a given identifier into sub-tokens based on camelCase and snake_case conventions.
    This function handles identifiers that may be in camelCase (e.g., `myVariableName`)
    or snake_case (e.g., `my_variable_name`). It splits them into individual words.
    """
    # 对驼峰和下划线命名进行拆分
    parts = re.sub('([a-z])([A-Z])', r'\1 \2', identifier).split()
    sub_parts = []
    for part in parts:
        sub_parts.extend(part.split('_'))
    return [p for p in sub_parts if p]

def process_code_tokens(code_str):
    """
    Tokenizes a given Python code string and processes the tokens.
    This function uses a Python lexer to tokenize the input code string. For each token:
    - If the token is an identifier (such as a variable or function name), it is further split into sub-tokens using the `split_identifier` function.
    - All tokens are converted to lowercase.
    Args:
        code_str (str): The Python code as a string to be tokenized and processed.
    Returns:
        List[str]: A list of processed tokens, where identifiers are split into sub-tokens and all tokens are lowercase.
    """

    lexer = get_lexer_by_name("python", stripall=True)
    tokens = lex(code_str, lexer)

    result_tokens = []
    for token_type, token in tokens:
        token = token.strip()
        if token:
            if token_type in [Token.Name, Token.Name.Function, Token.Name.Variable]:
                result_tokens.extend([t.lower() for t in split_identifier(token)])
            else:
                result_tokens.append(token.lower())
    return result_tokens


def edit_instruction_splitter(instr: str, tokenize: bool = True) -> tuple:
    """
    Splits an input string containing code and instruction sections, tokenizes each part, and returns the tokens.
    Args:
        instr (str): The input string containing code and instruction sections, formatted with
            '## Code Before:', '## Instruction:', and '## Code After:' delimiters.
        tokenize (bool): If True, returns tokenized code and instruction; if False, returns raw strings.
    Returns:
        tuple: A tuple (code_tokens, instr_tokens) where:
            - code_tokens (list or str): Tokens from the code section if tokenize is True, else raw code string.
            - instr_tokens (list or str): Tokens from the instruction section if tokenize is True, else raw instruction string.
    Note:
        - If the expected delimiters are not found, the corresponding output will be an empty string or list.
        - Code blocks wrapped in markdown (```) are stripped before tokenization.
    """

    # 提取代码部分
    code_match = re.search(r'## Code Before:(.*?)## Instruction:', instr, re.DOTALL)
    instr_match = re.search(r'## Instruction:(.*?)## Code After:', instr, re.DOTALL)
    code_str = code_match.group(1).strip() if code_match else ''
    # 去除 markdown 代码块包围
    if code_str.startswith("```") and code_str.endswith("```"):
        code_str = re.sub(r"^```[a-zA-Z]*\n?", "", code_str)
        code_str = re.sub(r"\n?```$", "", code_str)
        
    instr_str = instr_match.group(1).strip() if instr_match else ''

    if tokenize is False:
        return code_str, instr_str
    
    # 代码分词
    code_tokens = process_code_tokens(code_str)

    # 指令分词并去除标点，并转为小写
    instr_word_list = re.split(r'\s+', instr_str)
    instr_tokens = [re.sub(r'[^\w]', '', w).lower() for w in instr_word_list]
    instr_tokens = [w for w in instr_tokens if w]

    return code_tokens, instr_tokens


if __name__ == "__main__":
    # 示例代码字符串
    code_str_1 = """
def calculate_area(length, width):
    if length <= 0 or width <= 0:
        raise ValueError("Length and width must be positive")
    area = length * width
    return area

class Shape:
    def __init__(self, name):
        self.name = name

    def display_name(self):
        print(f"Shape name: {self.name}")

shape = Shape("Rectangle")
shape.display_name()
result = calculate_area(5, 3)
print(f"Area: {result}")
"""

    # 另一个示例代码字符串
    code_str_2 = """
def calculatePerimeter(length, width):
if length <= 0 or width <= 0:
    raise ValueError("Length and width must be positive")
perimeter = 2 * (length + width)
return perimeter

class RectangleShape:
def __init__(self, length, width):
    self.length = length
    self.width = width

def calculateArea(self):
    return self.length * self.width

def calculatePerimeter(self):
    return 2 * (self.length + self.width)

rectangle = RectangleShape(5, 3)
print(f"Area: {rectangle.calculateArea()}")
print(f"Perimeter: {rectangle.calculatePerimeter()}")
"""

    # 示例代码和自然语言混合字符串
    code_str_3 = """
# This function calculates the sum of two numbers
def add_numbers(a, b):
    # Ensure the inputs are numbers
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both inputs must be numbers")
    return a + b

# Example usage:
# The following line adds 10 and 20
result = add_numbers(10, 20)
print(f"The sum is: {result}")
"""

    code_str_4 = """
This function calculates the sum of two numbers

# Function
``` python
def add_numbers(a, b):
    # Ensure the inputs are numbers
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both inputs must be numbers")
    return a + b
```

"""

    code_str_5 = "## Code Before:\n```python\nimport os\nimport shutil\nimport cdsapi\n\nEXTENSIONS = {\n    'csv': '.csv',\n    'json': '.json',\n    'bin': '.bin'\n}\nSAMPLE_DATA_FOLDER = 'sample_data'\n\ndef download_dataset(dataset, request, name, format='bin'):\n    ext = EXTENSIONS.get(format, '.bin')\n    name = name.format(**locals())\n    path = os.path.join(SAMPLE_DATA_FOLDER, name)\n    if not os.path.exists(path):\n        c = cdsapi.Client()\n        try:\n            c.retrieve(dataset, request, target=path + '.tmp')\n            shutil.move(path + '.tmp', path)\n        except Exception as e:\n            print(f\"Error downloading {dataset}: {e}\")\n            return False\n    return True\n\ndef setup_package(version, readme_path='README.md', changes_path='CHANGES.md'):\n    try:\n        with open(readme_path) as f:\n            README = f.read()\n        with open(changes_path) as f:\n            CHANGES = f.read()\n    except IOError:\n        README = CHANGES = ''\n\n    setup(name='data_processor',\n          version=version,\n          description=\"Tool for processing and downloading datasets\",\n          long_description=README + \"\\n\" + CHANGES,\n          packages=['data_processor'],\n          install_requires=['cdsapi'])\n```\n## Instruction:\nThe current program has two main functions: `download_dataset` for downloading data files and `setup_package` for package configuration. There are several issues to address:\n1. The `download_dataset` function has a syntax error in its parameter list (extra closing parenthesis after `format='bin'`).\n2. The function doesn't create the `SAMPLE_DATA_FOLDER` directory if it doesn't exist, which could cause failures.\n3. The `setup_package` function references an undefined `setup` function (should be imported from setuptools).\n4. Error handling in `download_dataset` could be improved to distinguish between different types of failures.\n5. The program lacks proper documentation strings for its functions.\n\nModify the program to:\n- Fix the syntax error in `download_dataset`\n- Add directory creation for `SAMPLE_DATA_FOLDER`\n- Import and use `setuptools.setup` properly\n- Enhance error handling to provide more specific error messages\n- Add proper docstrings to both functions following Python conventions\n## Code After:\n"

    # 调用函数处理代码字符串
    # result_tokens = process_code_tokens(code_str_5)

    # result_str = " ".join(result_tokens)

    # print(result_tokens)
    # print(result_str)

    code_tokens, instr_tokens = edit_instruction_splitter(code_str_5)
    print("Code Tokens:", code_tokens)
    print("Instruction Tokens:", instr_tokens)
