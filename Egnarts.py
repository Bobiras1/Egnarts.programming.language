import os
import re
import sys
import math
import random

# Magical operators
operators = {
    '⚡': (4, lambda a: a ** 2),
    '☯': (3, lambda a, b: a * b),
    '☮': (3, lambda a, b: a / b if b != 0 else float('inf')),
    '✦': (2, lambda a, b: a + b),
    '✧': (2, lambda a, b: a - b),
    '<': (1, lambda a, b: a < b),
    '>': (1, lambda a, b: a > b),
    '<=': (1, lambda a, b: a <= b),
    '>=': (1, lambda a, b: a >= b),
    '==': (1, lambda a, b: a == b),
    '!=': (1, lambda a, b: a != b),
}

# Standard library
std_lib = {
    'rand': lambda: random.random(),
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
}

# Magical AI
def oraclo_response(prompt):
    return f"🔮 whispers: {prompt[::-1]}"

HELP_TEXT = """
✨ Magical egnarts Help ✨
- lumina "text" : print
- Operators: ✦ ✧ ☯ ☮ ⚡ < > <= >= == !=
- Loops: velora condition:
- Conditionals: krynn condition: ... sytha:
- Functions: aethera name(args): ... revara ... end
- AI: oraclo "question"
- Comments: ✨
- Multi-line expressions end with \
- exit / quit : leave REPL
- Variable assignment: x = expression
- End blocks with 'end'
"""

# Tokenizer
def tokenize(expr):
    # Match numbers, variables, operators, parentheses, commas, or strings
    pattern = r'"[^"]*"|\d+\.?\d*|[a-zA-Z_]\w*|==|!=|<=|>=|[✦✧☯☮⚡<>():,]'
    return re.findall(pattern, expr)

# Shunting Yard Parser
def parse_expression(tokens):
    output = []
    stack = []
    for token in tokens:
        if re.match(r'\d+\.?\d*', token) or (token.startswith('"') and token.endswith('"')):
            output.append(token)
        elif re.match(r'[a-zA-Z_]\w*', token):
            output.append(token)
        elif token in operators:
            while stack and stack[-1] != '(' and operators.get(stack[-1], (0,))[0] >= operators[token][0]:
                output.append(stack.pop())
            stack.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        elif token == ',':
            continue
    while stack:
        output.append(stack.pop())
    return output

# Evaluate RPN (handles strings safely)
def eval_rpn(rpn, env):
    stack = []
    for token in rpn:
        if re.match(r'\d+\.?\d*', str(token)):
            stack.append(float(token))
        elif isinstance(token, str):
            # Handle string literals
            if token.startswith('"') and token.endswith('"'):
                stack.append(token[1:-1])
            elif token in env:
                stack.append(env[token])
            elif token in std_lib:
                stack.append(std_lib[token]())
            elif token in operators:
                func = operators[token][1]
                if token == '⚡':
                    a = stack.pop()
                    if not isinstance(a, (int, float)):
                        raise TypeError(f"⚡ expects a number, got {type(a).__name__}")
                    stack.append(func(a))
                else:
                    b = stack.pop()
                    a = stack.pop()
                    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                        raise TypeError(f"{token} expects numbers, got {type(a).__name__}, {type(b).__name__}")
                    stack.append(func(a, b))
            else:
                raise ValueError(f"Unknown token: {token}")
    return stack[0] if stack else None

# Globals
file_lines = []
current_line = 0
functions = {}

# Block helpers
def collect_block():
    global current_line
    block = []
    while current_line < len(file_lines):
        line = file_lines[current_line].rstrip()
        current_line += 1
        if line == 'end':
            break
        block.append(line)
    return block

def execute_block(block, env):
    for line in block:
        result = evaluate(line, env)
        if isinstance(result, tuple) and result[0] == 'return':
            return result
    return None

def eval_condition(cond, env):
    tokens = tokenize(cond)
    rpn = parse_expression(tokens)
    return bool(eval_rpn(rpn, env))

def peek_next_line():
    global current_line
    if current_line < len(file_lines):
        return file_lines[current_line].strip()
    return ''

def skip_line():
    global current_line
    current_line += 1

# Evaluate a line
def evaluate(line, env):
    global functions
    line = line.strip()
    if not line or line.startswith('✨'):
        return
    # Print
    if line.startswith('lumina'):
        expr = line[6:].strip()
        tokens = tokenize(expr)
        rpn = parse_expression(tokens)
        value = eval_rpn(rpn, env)
        print(f"🪄 {value}")
    # AI
    elif line.startswith('oraclo'):
        prompt = line[6:].strip().strip('"')
        print(oraclo_response(prompt))
    # Help
    elif line == 'help':
        print(HELP_TEXT)
    # While loop
    elif line.startswith('velora '):
        condition = line[7:].rstrip(':').strip()
        block = collect_block()
        while eval_condition(condition, env):
            execute_block(block, env)
    # If / Else
    elif line.startswith('krynn '):
        condition = line[5:].rstrip(':').strip()
        if_block = collect_block()
        else_block = []
        if peek_next_line().startswith('sytha:'):
            skip_line()
            else_block = collect_block()
        if eval_condition(condition, env):
            execute_block(if_block, env)
        else:
            execute_block(else_block, env)
    # Function definition
    elif line.startswith('aethera '):
        name_args = line[7:].rstrip(':').strip()
        if '(' in name_args and ')' in name_args:
            name = name_args.split('(')[0].strip()
            args = name_args.split('(')[1].split(')')[0].split(',')
            args = [a.strip() for a in args if a.strip()]
            func_block = collect_block()
            functions[name] = (args, func_block)
    # Return
    elif line.startswith('revara '):
        expr = line[6:].strip()
        tokens = tokenize(expr)
        rpn = parse_expression(tokens)
        value = eval_rpn(rpn, env)
        return ('return', value)
    # Assignment
    elif '=' in line:
        var, expr = line.split('=', 1)
        var = var.strip()
        expr = expr.strip()
        if '(' in expr and ')' in expr:
            func_name = expr.split('(')[0].strip()
            arg_values = expr.split('(')[1].split(')')[0].split(',')
            arg_values = [eval_rpn(parse_expression(tokenize(a.strip())), env) for a in arg_values]
            if func_name in functions:
                func_args, func_block = functions[func_name]
                func_env = env.copy()
                for a, v in zip(func_args, arg_values):
                    func_env[a] = v
                result = execute_block(func_block, func_env)
                if isinstance(result, tuple) and result[0] == 'return':
                    env[var] = result[1]
                else:
                    env[var] = None
            else:
                print(f"Unknown function: {func_name}")
        else:
            tokens = tokenize(expr)
            rpn = parse_expression(tokens)
            env[var] = eval_rpn(rpn, env)
    # Expression
    else:
        if '(' in line and ')' in line:
            func_name = line.split('(')[0].strip()
            arg_values = line.split('(')[1].split(')')[0].split(',')
            arg_values = [eval_rpn(parse_expression(tokenize(a.strip())), env) for a in arg_values]
            if func_name in functions:
                func_args, func_block = functions[func_name]
                func_env = env.copy()
                for a, v in zip(func_args, arg_values):
                    func_env[a] = v
                result = execute_block(func_block, func_env)
                if isinstance(result, tuple) and result[0] == 'return':
                    print(result[1])
            else:
                print(f"Unknown function: {func_name}")
        else:
            tokens = tokenize(line)
            rpn = parse_expression(tokens)
            value = eval_rpn(rpn, env)
            print(value)

# Run file
def run_file(filename):
    global file_lines, current_line
    if not os.path.exists(filename):
        print(f"File {filename} does not exist.")
        return
    env = {}
    file_lines = open(filename, 'r', encoding='utf-8').readlines()
    current_line = 0
    while current_line < len(file_lines):
        evaluate(file_lines[current_line], env)
        current_line += 1

# REPL
def repl():
    global file_lines, current_line
    print("✨ Welcome to Magical egnarts REPL ✨")
    env = {}
    file_lines = []
    buffer = ''
    while True:
        try:
            line = input("egnarts> ")
            if line in ('exit', 'quit'):
                print("Goodbye! 🌙")
                break
            if line.endswith('\\'):
                buffer += line[:-1] + ' '
            else:
                buffer += line
                evaluate(buffer, env)
                buffer = ''
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt. Type 'exit' to quit.")
        except EOFError:
            print("\nEOF. Exiting.")
            break

# Main
if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()
