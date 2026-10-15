import argparse
import os
import re
import sys


class StackEmptyError(Exception):
    pass


class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if self.is_empty():
            raise StackEmptyError("pop from an empty stack")
        return self._items.pop()

    def peek(self):
        if self.is_empty():
            raise StackEmptyError("peek at an empty stack")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def __len__(self):
        return self.size()

    def __repr__(self):
        return f"Stack(bottom -> top: {self._items})"


class ExpressionError(ValueError):
    pass


NEG = "NEG"
PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, NEG: 3}
RIGHT_ASSOCIATIVE = {NEG}
BINARY_OPERATORS = {"+", "-", "*", "/"}


def tokenize(expression):
    tokens = []
    i = 0
    n = len(expression)

    while i < n:
        ch = expression[i]

        if ch.isspace():
            i += 1
            continue

        if ch.isdigit() or ch == ".":
            start = i
            while i < n and (expression[i].isdigit() or expression[i] == "."):
                i += 1
            text = expression[start:i]
            if text.count(".") > 1 or text == ".":
                raise ExpressionError(f"Invalid number '{text}'")
            tokens.append(float(text) if "." in text else int(text))
            continue

        if ch in BINARY_OPERATORS:
            previous = tokens[-1] if tokens else None
            is_unary = previous is None or previous == "(" or previous in PRECEDENCE
            if is_unary and ch == "-":
                tokens.append(NEG)
            elif is_unary and ch == "+":
                pass
            elif is_unary:
                raise ExpressionError(f"Operator '{ch}' is missing a left operand")
            else:
                tokens.append(ch)
            i += 1
            continue

        if ch in "()":
            tokens.append(ch)
            i += 1
            continue

        raise ExpressionError(f"Invalid character '{ch}' at position {i + 1}")

    return tokens


def apply_operator(operator, operands):
    try:
        if operator == NEG:
            operands.push(-operands.pop())
            return

        right = operands.pop()
        left = operands.pop()
    except StackEmptyError:
        symbol = "-" if operator == NEG else operator
        raise ExpressionError(f"Operator '{symbol}' is missing an operand") from None

    if operator == "+":
        result = left + right
    elif operator == "-":
        result = left - right
    elif operator == "*":
        result = left * right
    elif operator == "/":
        if right == 0:
            raise ExpressionError("Division by zero")
        result = left / right
    else:
        raise ExpressionError(f"Unknown operator '{operator}'")

    operands.push(result)


def should_apply_first(top, incoming):
    if top == "(":
        return False
    if PRECEDENCE[top] > PRECEDENCE[incoming]:
        return True
    if PRECEDENCE[top] == PRECEDENCE[incoming] and incoming not in RIGHT_ASSOCIATIVE:
        return True
    return False


def evaluate(expression):
    tokens = tokenize(expression)
    if not tokens:
        raise ExpressionError("Empty expression")

    operands = Stack()
    operators = Stack()

    for token in tokens:
        if isinstance(token, (int, float)):
            operands.push(token)

        elif token == "(":
            operators.push(token)

        elif token == ")":
            while not operators.is_empty() and operators.peek() != "(":
                apply_operator(operators.pop(), operands)
            if operators.is_empty():
                raise ExpressionError("Mismatched parentheses: unexpected ')'")
            operators.pop()

        else:
            while not operators.is_empty() and should_apply_first(operators.peek(), token):
                apply_operator(operators.pop(), operands)
            operators.push(token)

    while not operators.is_empty():
        top = operators.pop()
        if top == "(":
            raise ExpressionError("Mismatched parentheses: missing ')'")
        apply_operator(top, operands)

    if operands.size() != 1:
        raise ExpressionError("Malformed expression (missing operator between values)")

    return operands.pop()


def format_result(value):
    if isinstance(value, float):
        if value.is_integer():
            value = int(value)
        else:
            text = f"{value:.6f}".rstrip("0").rstrip(".")
            return "0" if text in ("-0", "") else text
    return str(value)


SEPARATOR_PATTERN = re.compile(r"^\s*([-=_~#])\1{2,}\s*$")


def is_separator(line):
    return bool(SEPARATOR_PATTERN.match(line))


def process_line(line):
    text = line.rstrip("\r\n")
    if is_separator(text):
        return text.strip()
    if text.strip() == "":
        return ""
    try:
        return format_result(evaluate(text))
    except ExpressionError as error:
        return f"ERROR: {error}"


def read_expressions(input_path):
    with open(input_path, "r", encoding="utf-8") as file:
        return file.read().splitlines()


def evaluate_lines(lines):
    return [process_line(line) for line in lines]


def write_results(output_path, results):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(results) + "\n")


def main(argv=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description="Evaluate mathematical expressions from a file using a stack."
    )
    parser.add_argument("input", nargs="?", default=os.path.join(script_dir, "input.txt"),
                        help="input file (default: input.txt next to this script)")
    parser.add_argument("output", nargs="?", default=os.path.join(script_dir, "output.txt"),
                        help="output file (default: output.txt next to this script)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print each expression and its result")
    args = parser.parse_args(argv)

    try:
        lines = read_expressions(args.input)
    except FileNotFoundError:
        print(f"Error: input file '{args.input}' was not found.", file=sys.stderr)
        return 1

    results = evaluate_lines(lines)
    write_results(args.output, results)

    evaluated = [(src, res) for src, res in zip(lines, results)
                 if src.strip() and not is_separator(src)]
    errors = sum(1 for _, res in evaluated if res.startswith("ERROR"))

    if args.verbose:
        width = max((len(src.strip()) for src, _ in evaluated), default=10)
        print(f"{'Expression'.ljust(width)}   Result")
        print("-" * (width + 12))
        for src, res in evaluated:
            print(f"{src.strip().ljust(width)}   {res}")
        print()

    print(f"Processed {len(evaluated)} expression(s): "
          f"{len(evaluated) - errors} evaluated, {errors} error(s).")
    print(f"Results written to '{args.output}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
