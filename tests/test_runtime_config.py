import os
import unittest
from unittest.mock import patch

from runtime_config import load_env


class RuntimeConfigTests(unittest.TestCase):
    def test_loads_literal_values_and_preserves_shell_overrides(self):
        content = (
            '# comment\nexport PROVIDER=openrouter\n'
            'MODEL="openai/gpt-4o-mini"\nOPENROUTER_API_KEY=\'dummy=a\'\n'
            'invalid line\n'
        )
        with patch.dict(os.environ, {'MODEL': 'shell-model'}, clear=True), \
                patch('runtime_config.Path.is_file', return_value=True), \
                patch('runtime_config.Path.read_text', return_value=content):
            load_env()
            self.assertEqual(os.environ['PROVIDER'], 'openrouter')
            self.assertEqual(os.environ['MODEL'], 'shell-model')
            self.assertEqual(os.environ['OPENROUTER_API_KEY'], 'dummy=a')

    def test_missing_file_is_optional(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch('runtime_config.Path.is_file', return_value=False):
            load_env()
            self.assertEqual(dict(os.environ), {})
