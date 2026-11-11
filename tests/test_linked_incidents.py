import unittest

from agent import linked_incidents, run_agent
from test_lab import FakeProvider, final, tool_call


class LinkedIncidentTests(unittest.TestCase):
    def test_only_supported_incident_urls_are_references(self):
        observation = {'updates': [{'body': (
            'See (https://www.githubstatus.com/incidents/related-123). '
            'https://www.githubstatus.com.evil.invalid/incidents/fake '
            'https://www.githubstatus.com/blog/other '
            'https://[broken/incidents/fake'
        )}]}
        self.assertEqual(linked_incidents(observation), {('github', 'related-123')})

    def test_unread_reference_requires_another_tool_step(self):
        class Tools:
            def execute(self, name, args):
                return {'ok': True, 'url': 'https://example.org/evidence',
                        'updates': [{'body': 'https://www.githubstatus.com/incidents/related-123'}]}

        fake = FakeProvider([
            tool_call('1', 'get_incident_details', '{"provider":"github","incident_id":"first"}'),
            final('Premature answer https://example.org/evidence'),
            tool_call('2', 'get_incident_details', '{"provider":"github","incident_id":"related-123"}'),
            final('Checked both https://example.org/evidence'),
        ])
        result = run_agent('Investigate', fake, Tools(), max_steps=4)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['answer'], 'Checked both https://example.org/evidence')
        self.assertEqual([e['event'] for e in result['trace']].count('validation_unread_incidents'), 1)
        self.assertIn('related-123', fake.histories[2][-1]['content'])

    def test_failed_reference_lookup_does_not_force_endless_retry(self):
        class Tools:
            def execute(self, name, args):
                if args['incident_id'] == 'related-123':
                    return {'ok': False, 'error': 'INCIDENT_NOT_FOUND'}
                return {'ok': True, 'url': 'https://example.org/evidence',
                        'updates': [{'body': 'https://www.githubstatus.com/incidents/related-123'}]}

        fake = FakeProvider([
            tool_call('1', 'get_incident_details', '{"provider":"github","incident_id":"first"}'),
            tool_call('2', 'get_incident_details', '{"provider":"github","incident_id":"related-123"}'),
            final('Related incident unavailable; source https://example.org/evidence'),
        ])
        self.assertEqual(run_agent('Investigate', fake, Tools(), max_steps=3)['status'], 'completed')

    def test_unread_reference_cannot_exceed_budget(self):
        class Tools:
            def execute(self, name, args):
                return {'ok': True, 'updates': [{'body': 'https://www.githubstatus.com/incidents/unread'}]}

        fake = FakeProvider([
            tool_call('1', 'get_incident_details', '{"provider":"github","incident_id":"first"}'),
            final('Premature answer'),
        ])
        result = run_agent('Investigate', fake, Tools(), max_steps=2)
        self.assertEqual(result['status'], 'max_steps')
        self.assertEqual(len(fake.histories), 2)
