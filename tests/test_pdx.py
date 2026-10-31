import unittest

from tools.pdx import Node, PdxSyntaxError, parse, walk


class TestPdx(unittest.TestCase):
    def test_simple_block(self):
        nodes = parse("a = { b = 1 }")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].key, "a")
        self.assertEqual(len(nodes[0].value), 1)
        kid = nodes[0].value[0]
        self.assertEqual((kid.key, kid.value, kid.line), ("b", "1", 1))

    def test_comment_and_string(self):
        self.assertEqual(parse('x = "a # b" # kommentar')[0].value, '"a # b"')

    def test_list_values(self):
        kids = parse("l = { A B }")[0].value
        self.assertEqual([k.value for k in kids], ["A", "B"])
        self.assertEqual([(k.key, k.op) for k in kids], [("", ""), ("", "")])

    def test_unbalanced_open(self):
        with self.assertRaises(PdxSyntaxError) as cm:
            parse("a = {\n  b = 1\n")
        self.assertEqual(cm.exception.line, 1)

    def test_unbalanced_close(self):
        with self.assertRaises(PdxSyntaxError) as cm:
            parse("a = 1\nb = 2\n}\n")
        self.assertEqual(cm.exception.line, 3)

    def test_comparison(self):
        kid = parse("check_variable = { v > 5 }")[0].value[0]
        self.assertEqual((kid.key, kid.op, kid.value), ("v", ">", "5"))

    def test_dotted_key_and_walk(self):
        nodes = parse("# c\nsov_cml.1 = { x = { y = 2 } }\nz = 3")
        self.assertEqual(nodes[0].key, "sov_cml.1")
        self.assertEqual([n.key for n in walk(nodes)], ["sov_cml.1", "x", "y", "z"])

    def test_bom_and_lines(self):
        nodes = parse("﻿a = 1\n\nb = 2")
        self.assertEqual([n.line for n in nodes], [1, 3])


if __name__ == "__main__":
    unittest.main()
