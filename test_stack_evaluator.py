import os
import tempfile
import unittest

from stack_evaluator import (
    Stack, StackEmptyError, ExpressionError,
    tokenize, evaluate, format_result, is_separator,
    process_line, read_expressions, evaluate_lines, write_results,
)


class TestStackOperations(unittest.TestCase):

    def test_new_stack_is_empty(self):
        s = Stack()
        self.assertTrue(s.is_empty())
        self.assertEqual(s.size(), 0)

    def test_push_increases_size(self):
        s = Stack()
        s.push(1)
        s.push(2)
        self.assertEqual(s.size(), 2)
        self.assertFalse(s.is_empty())

    def test_pop_returns_last_pushed_item_lifo(self):
        s = Stack()
        for item in (1, 2, 3):
            s.push(item)
        self.assertEqual(s.pop(), 3)
        self.assertEqual(s.pop(), 2)
        self.assertEqual(s.pop(), 1)
        self.assertTrue(s.is_empty())

    def test_peek_does_not_remove_item(self):
        s = Stack()
        s.push("a")
        self.assertEqual(s.peek(), "a")
        self.assertEqual(s.size(), 1)

    def test_pop_empty_stack_raises(self):
        with self.assertRaises(StackEmptyError):
            Stack().pop()

    def test_peek_empty_stack_raises(self):
        with self.assertRaises(StackEmptyError):
            Stack().peek()


class TestTokenizer(unittest.TestCase):

    def test_basic_tokens(self):
        self.assertEqual(tokenize("3 + 5 * 2"), [3, "+", 5, "*", 2])

    def test_parentheses_and_decimals(self):
        self.assertEqual(tokenize("(2.5+1)"), ["(", 2.5, "+", 1, ")"])

    def test_unary_minus(self):
        self.assertEqual(tokenize("-4 + 2"), ["NEG", 4, "+", 2])

    def test_invalid_character(self):
        with self.assertRaises(ExpressionError):
            tokenize("3 + a")


class TestEvaluation(unittest.TestCase):

    def test_assignment_example_1(self):
        self.assertEqual(evaluate("3 + 5 * 2"), 13)

    def test_assignment_example_2(self):
        self.assertEqual(evaluate("(8 / 4) + 7 * 2"), 16)

    def test_assignment_example_3(self):
        self.assertEqual(evaluate("10 - (2 + 3) * 4"), -10)

    def test_precedence(self):
        self.assertEqual(evaluate("2 + 3 * 4"), 14)
        self.assertEqual(evaluate("2 * 3 + 4"), 10)

    def test_left_associativity(self):
        self.assertEqual(evaluate("20 - 6 - 4"), 10)
        self.assertEqual(evaluate("100 / 10 / 5"), 2)

    def test_nested_parentheses(self):
        self.assertEqual(evaluate("((15 / (7 - (1 + 1))) * 3) - (2 + (1 + 1))"), 5)

    def test_decimal_result(self):
        self.assertEqual(evaluate("100 / 8"), 12.5)

    def test_unary_minus(self):
        self.assertEqual(evaluate("-4 + 2 * (3 - 1)"), 0)
        self.assertEqual(evaluate("3 * -(2 + 1)"), -9)

    def test_division_by_zero(self):
        with self.assertRaises(ExpressionError):
            evaluate("7 / 0")

    def test_missing_closing_parenthesis(self):
        with self.assertRaises(ExpressionError):
            evaluate("(3 + 4 * 2")

    def test_unexpected_closing_parenthesis(self):
        with self.assertRaises(ExpressionError):
            evaluate("3 + 4)")

    def test_missing_operand(self):
        with self.assertRaises(ExpressionError):
            evaluate("3 +")

    def test_missing_operator(self):
        with self.assertRaises(ExpressionError):
            evaluate("3 4")

    def test_empty_expression(self):
        with self.assertRaises(ExpressionError):
            evaluate("   ")


class TestFormatting(unittest.TestCase):

    def test_whole_float_printed_as_integer(self):
        self.assertEqual(format_result(16.0), "16")

    def test_decimal_rounded_and_trimmed(self):
        self.assertEqual(format_result(12.5), "12.5")
        self.assertEqual(format_result(10 / 3), "3.333333")


class TestFileHandling(unittest.TestCase):

    def test_separator_detection(self):
        self.assertTrue(is_separator("-----"))
        self.assertTrue(is_separator("  =====  "))
        self.assertFalse(is_separator("3 - 2"))
        self.assertFalse(is_separator("-"))

    def test_process_line_keeps_separator(self):
        self.assertEqual(process_line("-----"), "-----")

    def test_process_line_reports_error(self):
        self.assertTrue(process_line("7 / 0").startswith("ERROR"))

    def test_full_file_round_trip(self):
        content = "3 + 5 * 2\n-----\n(8 / 4) + 7 * 2\n-----\n10 - (2 + 3) * 4\n"
        with tempfile.TemporaryDirectory() as folder:
            in_path = os.path.join(folder, "input.txt")
            out_path = os.path.join(folder, "output.txt")
            with open(in_path, "w", encoding="utf-8") as f:
                f.write(content)

            write_results(out_path, evaluate_lines(read_expressions(in_path)))

            with open(out_path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "13\n-----\n16\n-----\n-10\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
