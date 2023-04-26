from unittest import TestCase
from packed_udvts import util


class TestUtil(TestCase):
    def test_to_camel_case(self):
        self.assertEqual(util.to_camel_case("foo"), "foo")
        self.assertEqual(util.to_camel_case("foo_bar"), "fooBar")
        self.assertEqual(util.to_camel_case("foo_bar_baz"), "fooBarBaz")

    def test_to_title_case(self):
        self.assertEqual(util.to_title_case("foo"), "Foo")
        self.assertEqual(util.to_title_case("foo_bar"), "FooBar")
        self.assertEqual(util.to_title_case("foo_bar_baz"), "FooBarBaz")
