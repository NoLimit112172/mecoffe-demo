"""Generate independent, fictional public fixtures. No private data is read."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_URL = 'https://github.com/NoLimit112172/mecoffe-demo'
ROLE_LABELS = {'merchant': '咖啡商家', 'undergraduate_consumer': '本科生',
               'graduate_consumer': '研究生', 'teacher_consumer': '教师'}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def make_snapshot(config):
    nodes = []
    for number in (1, 2):
        nodes.append({'entity_id': f'merchant_{number:03}', 'role': 'merchant',
                      'name': f'示例咖啡{chr(64 + number)}',
                      'description': '公开演示中的虚构咖啡商家，不对应实际经营主体。',
                      'static_attributes': {'gender': 'female' if number == 1 else 'male', 'age': 36},
                      'dynamic_attributes': {'promotion_goal': '演示商品信息如何沿合成关注网络传播。'}})
    for role, prefix, count, minimum_age in (
        ('undergraduate_consumer', 'public_undergrad', 70, 18),
        ('graduate_consumer', 'public_graduate', 20, 23),
        ('teacher_consumer', 'public_teacher', 8, 31),
    ):
        for index in range(1, count + 1):
            label = ROLE_LABELS[role]
            nodes.append({'entity_id': f'{prefix}_{index:03}', 'role': role,
                          'name': f'{label}{index:02}',
                          'description': f'独立生成的{label}示例人物，所有属性均为虚构。',
                          'static_attributes': {'gender': 'female' if index % 2 else 'male',
                                                'age': minimum_age + index % 4},
                          'dynamic_attributes': {
                              'coffee_preferences': [['美式'], ['拿铁'], ['无糖咖啡']][index % 3],
                              'coffee_budget_30d_cny': [96, 132, 168][index % 3],
                              'personality': ['示例：关注预算', '示例：愿意了解新品', '示例：关注同伴消息'][index % 3],
                              'purchase_strategy': '公开规则演示：获知品牌且示例余额充足时，按配置抽样购买。',
                          }})
    consumers = [node['entity_id'] for node in nodes if node['role'] != 'merchant']
    rng = random.Random(config['network_seed'])
    edges = []
    for source in consumers:
        for target in sorted(rng.sample([value for value in consumers if value != source], 5)):
            edges.append({'source': source, 'target': target, 'relation': 'follow'})
    for merchant in ('merchant_001', 'merchant_002'):
        for source in sorted(rng.sample(consumers, 20)):
            edges.append({'source': source, 'target': merchant, 'relation': 'follow'})
    return {'schema_version': '1.0', 'snapshot_id': 'snapshot_public_demo_100',
            'snapshot_revision': 1, 'dataset_kind': 'public_synthetic', 'public_synthetic': True,
            'provenance': {'origin': 'independently_generated_fixture', 'source_url': SOURCE_URL,
                           'network_seed': config['network_seed'],
                           'note': '所有人物、属性与关系均由此公开脚本独立生成，不对应真实人员或已执行实验。'},
            'nodes': nodes, 'edges': edges}


def assign_buildings(people, campus):
    buildings = {building['building_id']: location['location_id']
                 for location in campus['locations'] for building in location.get('buildings', [])}
    for role in ROLE_LABELS:
        members = [person for person in people if person['role'] == role]
        if role == 'merchant':
            for person in members:
                location = next(value for value in campus['locations'] if value.get('brand_id') == person['id'])
                person.update(home_location_id=location['location_id'],
                              building_id=location['buildings'][0]['building_id'], indoor=False)
            continue
        rules = campus['occupancy'][role]
        total = sum(rule['share'] for rule in rules)
        raw = [len(members) * rule['share'] / total for rule in rules]
        counts = [int(value) for value in raw]
        for index in sorted(range(len(raw)), key=lambda i: (raw[i] - counts[i], -i), reverse=True)[:len(members) - sum(counts)]:
            counts[index] += 1
        ordered = sorted(members, key=lambda person: hashlib.sha256(person['id'].encode()).hexdigest())
        cursor = 0
        for rule, count in zip(rules, counts):
            for person in ordered[cursor:cursor + count]:
                person.update(building_id=rule['building_id'],
                              home_location_id=buildings[rule['building_id']], indoor=True)
            cursor += count


def make_network(snapshot, campus):
    people = []
    for node in snapshot['nodes']:
        static, profile = node['static_attributes'], node['dynamic_attributes']
        people.append({'id': node['entity_id'], 'role': node['role'], 'role_label': ROLE_LABELS[node['role']],
                       'name': node['name'], 'gender': 'f' if static['gender'] == 'female' else 'm',
                       'age': static['age'], 'bio': node['description'], 'profile': copy.deepcopy(profile)})
    assign_buildings(people, campus)
    brands = [{'brand_id': node['entity_id'], 'merchant_id': node['entity_id'], 'product_name': node['name'],
               'location_id': next(value['location_id'] for value in campus['locations']
                                   if value.get('brand_id') == node['entity_id'])}
              for node in snapshot['nodes'] if node['role'] == 'merchant']
    digest = lambda value: hashlib.sha256(json_bytes(value)).hexdigest()
    return {'schema': 'mecoffe.scene.v1',
            'meta': {'mode': 'network_snapshot', 'dataset_kind': 'public_synthetic',
                     'public_synthetic': True, 'illustrative': True, 'status': 'not_run',
                     'execution_status': 'not_run', 'run_id': None,
                     'snapshot_id': snapshot['snapshot_id'], 'snapshot_revision': 1,
                     'completed_steps': 0, 'total_steps': 0, 'source_url': SOURCE_URL,
                     'sources': {'snapshot_sha256': digest(snapshot), 'campus_sha256': digest(campus)},
                     'disclaimer': '公开独立合成示例，不对应真实人员、市场或 OASIS 实验结果。'},
            'summary': {'people': len(people), 'relationships': len(snapshot['edges']), 'events': 0,
                        'orders': 0, 'revenue_fen': 0, 'by_type': {}, 'noop': 0, 'illustrative': True},
            'campus': campus, 'brands': brands, 'people': people,
            'relationships': copy.deepcopy(snapshot['edges']), 'posts': {}, 'events': [],
            'days': [{'step': 0, 'label': '公开示例网络', 'complete': True, 'noop': 0, 'counts': {}}]}


def make_demo(network, config):
    scene = copy.deepcopy(network)
    rng = random.Random(config['event_seed'])
    consumers = {person['id']: person for person in scene['people'] if person['role'] != 'merchant'}
    brands = {brand['brand_id']: brand for brand in scene['brands']}
    followers = defaultdict(list)
    for edge in scene['relationships']:
        followers[edge['target']].append(edge['source'])
    for audience in followers.values():
        audience.sort()
    known = {person: set() for person in consumers}
    budgets = {person: int(data['profile']['coffee_budget_30d_cny'] * 100) for person, data in consumers.items()}
    initial_budgets = dict(budgets)
    events, posts, days = [], {}, []
    sequence = 0

    def emit(day, kind, actor, stage, **fields):
        record = {'key': f'public-demo:{day}:{len(events) + 1}', 'step': day, 'type': kind,
                  'actor': actor, 'stage': stage, 'origin': 'public_synthetic_script',
                  'illustrative': True, 'public_synthetic': True, **fields}
        events.append(record)
        return record

    for day in range(1, config['days'] + 1):
        start = len(events)
        if (day - 1) % config['advertisement_interval_days'] == 0:
            for brand_id, brand in sorted(brands.items()):
                audience = rng.sample(followers[brand_id], min(config['advertisement_recipients'], len(followers[brand_id])))
                post_id = f'public-ad:{day}:{brand_id}'
                advertisement = emit(day, 'ad', brand['merchant_id'], 'merchant_operations', brand_id=brand_id,
                                     post_id=post_id, targeted=audience,
                                     text=f"[公开示例] {brand['product_name']} 的虚构推广信息。")
                posts[post_id] = {'author': brand['merchant_id'], 'content': advertisement['text'], 'brand_id': brand_id}
                for person in audience:
                    emit(day, 'exposure', person, 'feed', target=brand['merchant_id'],
                         brand_ids=[brand_id], post_ids=[post_id])
                    known[person].add(brand_id)
        candidates = [person for person in sorted(consumers)
                      if any(budgets[person] >= config['prices_fen'][brand] for brand in known[person])]
        rng.shuffle(candidates)
        purchases_today = 0
        for person in candidates:
            if purchases_today >= config['max_purchases_per_day']:
                break
            if rng.random() > config['purchase_probability']:
                continue
            available = sorted(brand for brand in known[person] if budgets[person] >= config['prices_fen'][brand])
            brand_id = rng.choice(available)
            brand = brands[brand_id]
            amount = config['prices_fen'][brand_id]
            budgets[person] -= amount
            purchases_today += 1
            sequence += 1
            emit(day, 'purchase', person, 'consumer_purchase', brand_id=brand_id,
                 order_id=f'public-order:{sequence}', quantity=1, amount_fen=amount,
                 product_name=brand['product_name'])
            post_id = f'public-post:{sequence}'
            post = emit(day, 'post', person, 'social_exchange', brand_id=brand_id, post_id=post_id,
                        text=f"[公开示例] 到 {brand['product_name']} 柜台购买一杯示例咖啡，再返回所在楼栋。")
            posts[post_id] = {'author': person, 'content': post['text'], 'brand_id': brand_id}
            if followers[person]:
                recipient = rng.choice(followers[person])
                emit(day, 'comment', recipient, 'social_exchange', target=person, post_id=post_id,
                     brand_id=brand_id, text='[公开示例] 从关注对象的消息中了解到这家虚构咖啡店。')
                known[recipient].add(brand_id)
        days.append({'step': day, 'label': f'演示第 {day} 天', 'complete': True, 'noop': 0,
                     'counts': dict(sorted(Counter(event['type'] for event in events[start:]).items()))})
    scene['meta'].update({'mode': 'network_demo', 'status': 'demo', 'completed_steps': config['days'],
                          'total_steps': config['days'], 'step_unit': 'synthetic_demo_day',
                          'demo_duration_days': config['days'], 'demo_config': copy.deepcopy(config),
                          'demo_budget_fen': initial_budgets, 'demo_remaining_budget_fen': budgets,
                          'limitations': ['演示日数只是脚本长度，不代表已执行的 OASIS 实验。',
                                          '价格、预算、概率和传播规则均为公开的虚构示例。']})
    purchases = [event for event in events if event['type'] == 'purchase']
    scene.update(events=events, posts=posts, days=days,
                 summary={'people': len(scene['people']), 'relationships': len(scene['relationships']),
                          'events': len(events), 'orders': len(purchases),
                          'revenue_fen': sum(event['amount_fen'] for event in purchases),
                          'by_type': dict(sorted(Counter(event['type'] for event in events).items())),
                          'noop': 0, 'illustrative': True, 'public_synthetic': True})
    return scene


def generate(root=ROOT):
    config = json.loads((root / 'scene/public-demo.json').read_text(encoding='utf-8'))
    campus = json.loads((root / 'scene/campus.json').read_text(encoding='utf-8'))
    campus.update(campus_id='public_synthetic_campus', title='公开示例校园',
                  note='独立公开示例的虚构校园布局；地点和移动只用于展示，不对应任何真实学校或人员行踪。')
    for location in campus['locations']:
        if location.get('brand_id') in ('merchant_001', 'merchant_002'):
            name = '示例咖啡A' if location['brand_id'] == 'merchant_001' else '示例咖啡B'
            location['name'] = name
            for building in location.get('buildings', []):
                building['name'] = name
    write_json(root / 'scene/campus.json', campus)
    snapshot = make_snapshot(config)
    network = make_network(snapshot, campus)
    demo = make_demo(network, config)
    write_json(root / 'data/population_snapshot.json', snapshot)
    write_json(root / 'public/mecoffe/latest-network.json', network)
    write_json(root / 'public/mecoffe/latest-demo.json', demo)
    return snapshot, network, demo


if __name__ == '__main__':
    snapshot, network, demo = generate()
    print(f"Public synthetic fixtures: {len(snapshot['nodes'])} people, {len(snapshot['edges'])} follows, "
          f"{len(demo['days'])} scripted days, {len(demo['events'])} events. No private input was read.")
