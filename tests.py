#!/usr/bin/env python

import unittest

from pyvn import pyvn as api


@api
class VersionedClass(object):

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


@api
class Story(object):
    """These are some pretty unlikely or bad examples"""

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
    def format():
        return 'xml'

    @staticmethod
    @api('version', 2)
    def format():
        return 'json'


class TestStories(unittest.TestCase):

    def setUp(self):
        self.story = Story(1, 'hello')

    def test_pyvn(self):

        #print Story.list_v2

        self.assertEqual(self.story.get_v1(), '<xml id="1">hello</xml>')
        self.assertEqual(self.story.get_v2(), '{id=1, content: "hello"}')
        self.assertEqual(self.story.get_v3(), '{id=1, content: "hello"}')


class TestPyvn(unittest.TestCase):

    def test_versions(self):

        obj = VersionedClass()

        # The "basic" method starts at v2.
        # It should not work if requesting v1.
        try:
            obj.basic_v1
            self.fail('This should not be implemented.')
        except NotImplementedError:
            pass

        # Anything from v2 and above should work, even if not defined.
        # The fallback logic drops down to the next highest version.
        self.assertTrue(hasattr(obj, 'basic_v2'))
        self.assertTrue(hasattr(obj, 'basic_v3'))
        self.assertTrue(hasattr(obj, 'basic_v4'))

        # Check that the content is as expected.
        self.assertEqual(obj.basic_v2(), 'this is basic_v2')
        self.assertEqual(obj.basic_v3('testing v3'), "this is basic_v3 with 'testing v3'")
        self.assertEqual(obj.basic_v100('testing v100'), "this is basic_v3 with 'testing v100'")

    def test_namespaces(self):

        obj = VersionedClass()

        # Check that the "api" namespace is working.
        self.assertTrue(hasattr(obj, 'api'))
        self.assertTrue(hasattr(obj.api, 'test_v1'))
        self.assertTrue(hasattr(obj.api, 'test_v5'))
        self.assertEqual(obj.api.test_v5(), 'namespace_two')

        # Check that the nested namespace is working.
        self.assertTrue(hasattr(obj.api, 'test'))
        self.assertTrue(hasattr(obj.api.test, 'third_v50'))
        self.assertEqual(obj.api.test.third_v55(), 'nested works')

        # Check that no namespace still works.
        self.assertFalse(hasattr(obj, 'basic_v1'))
        self.assertTrue(hasattr(obj, 'basic_v2'))
        self.assertEqual(obj.basic_v2(), 'this is basic_v2')

        # And for good measure...
        try:
            obj.one.two.three.four.stop_v3
            self.fail('This should not be implemented.')
        except NotImplementedError:
            pass
        self.assertEqual(obj.one.two.three.four.stop_v5(), 'ridiculous nesting')


if __name__ == '__main__':
    unittest.main()
