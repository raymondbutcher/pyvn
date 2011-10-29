#!/usr/bin/env python

import unittest

from pyvn import pyvn as api


class TestClassMethods(unittest.TestCase):
    """Tests for classmethods and staticmethods."""

    class Story(api.Class):
        """These are some pretty unlikely and bad examples."""

        def __init__(self, id, content):
            self.id = id
            self.content = content

        @classmethod
        @api('list', 2)
        def list_json(cls):
            return '{example: null}'

        @api('get', 1)
        def get_xml(self):
            return '<xml id="%d">%s</xml>' % (self.id, self.content)

        @api('get', 2)
        def get_json(self):
            return '{id=%d, content: "%s"}' % (self.id, self.content)

        @staticmethod
        @api('version', 1)
        def xml_version():
            return 1, 'xml'

        @staticmethod
        @api('version', 2)
        def json_version():
            return 2, 'json'

        @property
        @api('title', 2)
        def title(self):
            return 'who knows'

    def setUp(self):
        self.story = self.Story(1, 'hello')

    def test_methods(self):

        # Instance methods.
        self.assertEqual(self.story.get_v1(), '<xml id="1">hello</xml>')
        self.assertEqual(self.story.get_v2(), '{id=1, content: "hello"}')
        self.assertEqual(self.story.get_v3(), '{id=1, content: "hello"}')

        # Class methods.
        self.assertEqual(self.Story.list_v2(), '{example: null}')
        self.assertEqual(self.Story.list_v5(), '{example: null}')
        # Access it via the instance too.
        self.assertEqual(self.story.list_v2(), '{example: null}')
        try:
            self.Story.list_v1()
            self.fail('This should not be implemented')
        except NotImplementedError:
            pass

        # Static methods.
        self.assertEqual(self.Story.version_v1(), (1, 'xml'))
        self.assertEqual(self.Story.version_v2(), (2, 'json'))

        # Property methods.
        try:
            self.story.title_v1
            self.fail('This should not be implemented')
        except NotImplementedError:
            pass
        self.assertEqual(self.story.title_v2, 'who knows')
        self.assertEqual(self.story.title_v3, 'who knows')


class TestEverything(unittest.TestCase):

    class NamespaceExample(api.Class):

        @api('basic', 2)    
        def basic_two(self):
            return 'this is basic_v2'

        @api('basic', 3)    
        def basic_three(self, new_argument):
            return 'this is basic_v3 with %r' % new_argument

        @api('api.test', 1)
        def namespace_one(self):
            return 'namespace_one'

        @api('api.test', 2)
        def namespace_two(self):
            return 'namespace_two'

        @api('api.test.third', 50)
        def nested(self):
            return 'nested works'

        @api('one.two.three.four.stop', 5)
        def ridiculous(self):
            return 'ridiculous nesting'

    def setUp(self):
        self.obj = self.NamespaceExample()

    def test_versions(self):

        # The "basic" method starts at v2.
        # It should not work if requesting v1.
        try:
            self.obj.basic_v1
            self.fail('This should not be implemented.')
        except NotImplementedError:
            pass

        # Anything from v2 and above should work, even if not defined.
        # The fallback logic drops down to the next highest version.
        self.assertTrue(hasattr(self.obj, 'basic_v2'))
        self.assertTrue(hasattr(self.obj, 'basic_v3'))
        self.assertTrue(hasattr(self.obj, 'basic_v4'))

        # Check that the content is as expected.
        self.assertEqual(self.obj.basic_v2(), 'this is basic_v2')
        self.assertEqual(self.obj.basic_v3('testing v3'), "this is basic_v3 with 'testing v3'")
        self.assertEqual(self.obj.basic_v100('testing v100'), "this is basic_v3 with 'testing v100'")

    def test_namespaces(self):

        # Check that the "api" namespace is working.
        self.assertTrue(hasattr(self.obj, 'api'))
        self.assertTrue(hasattr(self.obj.api, 'test_v1'))
        self.assertTrue(hasattr(self.obj.api, 'test_v5'))
        self.assertEqual(self.obj.api.test_v5(), 'namespace_two')

        # Check that the nested namespace is working.
        self.assertTrue(hasattr(self.obj.api, 'test'))
        self.assertTrue(hasattr(self.obj.api.test, 'third_v50'))
        self.assertEqual(self.obj.api.test.third_v55(), 'nested works')

        # And for good measure...
        try:
            self.obj.one.two.three.four.stop_v3
            self.fail('This should not be implemented.')
        except NotImplementedError:
            pass
        self.assertEqual(self.obj.one.two.three.four.stop_v5(), 'ridiculous nesting')


class TestMultipleNames(unittest.TestCase):
    """I don't know why anyone would do this but it works."""

    class Multipass(api.Class):

        @api('multi.dogs', 1)
        @api('multi.cats', 1)
        def multipass(self, what):
            return 'multipass %s' % what

        @classmethod
        @api('multi.rabbit', 1)
        @api('multi.buffalo', 2)
        def complicated(cls):
            return 'ok'

    def setUp(self):
        self.obj = self.Multipass()

    def test_multiple_names(self):

        self.assertEqual(self.obj.multi.dogs_v1('aaa'), 'multipass aaa')
        self.assertEqual(self.obj.multi.cats_v1('bbb'), 'multipass bbb')

        self.assertEqual(self.obj.multi.rabbit_v1(), 'ok')
        try:
            self.Multipass.multi.buffalo_v1()
            self.fail('This should not be implemented')
        except NotImplementedError:
            pass
        self.assertEqual(self.obj.multi.buffalo_v2(), 'ok')


if __name__ == '__main__':
    unittest.main()
