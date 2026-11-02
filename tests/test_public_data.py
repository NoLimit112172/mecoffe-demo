import copy
import json
import re
import unittest
from collections import Counter

from scripts.generate_public_data import ROOT, SOURCE_URL, make_demo, make_network, make_snapshot


class PublicDataCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / 'scene/public-demo.json').read_text(encoding='utf-8'))
        cls.campus = json.loads((ROOT / 'scene/campus.json').read_text(encoding='utf-8'))
        cls.snapshot = make_snapshot(cls.config)
        cls.network = make_network(cls.snapshot, cls.campus)
        cls.demo = make_demo(cls.network, cls.config)

    def test_only_independent_public_identities_and_provenance(self):
        snapshot = self.snapshot
        self.assertEqual(snapshot['snapshot_id'], 'snapshot_public_demo_100')
        self.assertEqual(snapshot['dataset_kind'], 'public_synthetic')
        self.assertTrue(snapshot['public_synthetic'])
        self.assertEqual(len(snapshot['nodes']), 100)
        for person in snapshot['nodes']:
            self.assertRegex(person['entity_id'], r'^(merchant_00[12]|public_(undergrad|graduate|teacher)_\d{3})$')
            self.assertRegex(person['name'], r'^(示例咖啡[AB]|(本科生|研究生|教师)\d{2})$')
            self.assertIn('虚构', person['description'])
        for scene in (self.network, self.demo):
            self.assertEqual(scene['meta']['source_url'], SOURCE_URL)
            self.assertTrue(scene['meta']['public_synthetic'])
            self.assertTrue(scene['meta']['illustrative'])
            self.assertIsNone(scene['meta']['run_id'])
            self.assertEqual(scene['meta']['dataset_kind'], 'public_synthetic')
            self.assertEqual(scene['relationships'], snapshot['edges'])

    def test_network_has_no_dangling_self_or_duplicate_edges(self):
        people = {person['entity_id']: person for person in self.snapshot['nodes']}
        edges = self.snapshot['edges']
        triples = {(edge['source'], edge['target'], edge['relation']) for edge in edges}
        self.assertEqual(len(edges), 530)
        self.assertEqual(len(triples), 530)
        peer_counts, merchant_fans = Counter(), Counter()
        for source, target, relation in triples:
            self.assertIn(source, people)
            self.assertIn(target, people)
            self.assertNotEqual(source, target)
            self.assertEqual(relation, 'follow')
            self.assertNotEqual(people[source]['role'], 'merchant')
            if people[target]['role'] == 'merchant':
                merchant_fans[target] += 1
            else:
                peer_counts[source] += 1
        self.assertEqual(len(peer_counts), 98)
        self.assertEqual(set(peer_counts.values()), {5})
        self.assertEqual(merchant_fans, {'merchant_001': 20, 'merchant_002': 20})

    def test_spread_uses_real_public_follows_and_precedes_purchase(self):
        follows = {(edge['source'], edge['target']) for edge in self.snapshot['edges']}
        known = {person['id']: set() for person in self.demo['people'] if person['role'] != 'merchant'}
        posts = {}
        for event in self.demo['events']:
            self.assertTrue(event['public_synthetic'])
            self.assertTrue(event['illustrative'])
            self.assertEqual(event['origin'], 'public_synthetic_script')
            if event['type'] == 'ad':
                self.assertTrue(all((person, event['actor']) in follows for person in event['targeted']))
            elif event['type'] == 'exposure':
                self.assertIn((event['actor'], event['target']), follows)
                known[event['actor']].update(event['brand_ids'])
            elif event['type'] == 'purchase':
                self.assertIn(event['brand_id'], known[event['actor']])
            elif event['type'] == 'post':
                posts[event['post_id']] = event
            elif event['type'] == 'comment':
                self.assertIn((event['actor'], event['target']), follows)
                self.assertEqual(posts[event['post_id']]['actor'], event['target'])
                known[event['actor']].add(event['brand_id'])
        self.assertFalse(any(event['type'] == 'interview' for event in self.demo['events']))

    def test_order_totals_budget_and_timeline_reconcile(self):
        demo = self.demo
        self.assertEqual([day['step'] for day in demo['days']], list(range(1, 31)))
        seen, spent, daily = set(), Counter(), Counter()
        for event in demo['events']:
            if event['type'] != 'purchase':
                continue
            self.assertNotIn(event['order_id'], seen)
            seen.add(event['order_id'])
            self.assertEqual(event['quantity'], 1)
            self.assertEqual(event['amount_fen'], self.config['prices_fen'][event['brand_id']])
            spent[event['actor']] += event['amount_fen']
            daily[event['step']] += 1
        self.assertEqual(len(seen), demo['summary']['orders'])
        self.assertEqual(sum(spent.values()), demo['summary']['revenue_fen'])
        self.assertTrue(all(count <= self.config['max_purchases_per_day'] for count in daily.values()))
        for person, amount in spent.items():
            self.assertLessEqual(amount, demo['meta']['demo_budget_fen'][person])
            self.assertEqual(demo['meta']['demo_budget_fen'][person] - amount,
                             demo['meta']['demo_remaining_budget_fen'][person])

    def test_generation_is_reproducible_and_network_changes_affect_behavior(self):
        self.assertEqual(self.snapshot, make_snapshot(self.config))
        self.assertEqual(self.demo, make_demo(self.network, self.config))
        changed = copy.deepcopy(self.config)
        changed['network_seed'] += 17
        altered_snapshot = make_snapshot(changed)
        self.assertNotEqual(self.snapshot['edges'], altered_snapshot['edges'])
        altered_demo = make_demo(make_network(altered_snapshot, self.campus), changed)
        self.assertNotEqual(self.demo['events'], altered_demo['events'])


if __name__ == '__main__':
    unittest.main()
