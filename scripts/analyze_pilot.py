"""Descriptive first-pilot analysis; the source verifier must accept the sealed run."""
import json
from collections import defaultdict
from pathlib import Path
import sys

from baseline.finalize import verify_finalization
from baseline.protocol import CHOICE_FAMILIES, NUMERIC_FAMILIES
from baseline.statistics import family_metrics

report = verify_finalization(sys.argv[1])
rows = [dict(entry['result'], model_id=entry['model_id']) for entry in report['results'] if entry['included_in_comparison']]
items = {item['task_id']: item for item in report['specimens']}
analysis = {
    'release': report['release'],
    'run_id': report['run_id'],
    'campaign': report['campaign'],
    'scope': 'Descriptive results on this fixed pilot; no independent-observation or population inference.',
    'model_count': len(report['comparison']['model_ids']),
    'question_count': report['comparison']['count'],
    'group_count': len({items[task]['group_id'] for task in report['comparison']['task_ids']}),
    'families': {},
    'matching_binding_pairs': {},
    'numeric_format_pairs': {},
}
for family in CHOICE_FAMILIES + NUMERIC_FAMILIES:
    selected = [row for row in rows if row['family'] == family]
    overall = family_metrics(selected, family)
    models = []
    for model in report['models']:
        value = model['families'][family]
        models.append({'id': model['model_id'], 'name': model['model_config']['display_name'], **value})
    models.sort(key=lambda model: (-(model['accuracy'] if family in CHOICE_FAMILIES else model['mean_score']), model['id']))
    slices = {}
    for dimension in ['difficulty', 'axis']:
        slices[dimension] = {value: family_metrics([row for row in selected if items[row['task_id']]['design'].get(dimension) == value], family)
                             for value in sorted({items[row['task_id']]['design'].get(dimension) for row in selected})}
    analysis['families'][family] = {'responses_across_models': overall, 'models': models, 'slices': slices}
paired = defaultdict(dict)
for row in rows:
    paired[(row['model_id'], row['group_id'])][row['family']] = row
for model in report['comparison']['model_ids']:
    groups = [value for (name, _), value in paired.items() if name == model and 'matching' in value and 'binding' in value]
    analysis['matching_binding_pairs'][model] = {
        'count': len(groups),
        'both_correct': sum(pair['matching']['correct'] and pair['binding']['correct'] for pair in groups),
        'matching_only_correct': sum(pair['matching']['correct'] and not pair['binding']['correct'] for pair in groups),
        'binding_only_correct': sum(pair['binding']['correct'] and not pair['matching']['correct'] for pair in groups),
        'both_incorrect': sum(not pair['matching']['correct'] and not pair['binding']['correct'] for pair in groups),
    }
for first, second in [('rgb', 'hsl'), ('rgb', 'oklch'), ('hsl', 'oklch')]:
    pairs = [group for group in paired.values() if first in group and second in group and group[first]['valid'] and group[second]['valid']]
    diffs = [pair[first]['delta_e_ok'] - pair[second]['delta_e_ok'] for pair in pairs]
    analysis['numeric_format_pairs'][f'{first}_vs_{second}'] = {
        'valid_pairs': len(pairs), 'first_lower_error': sum(difference < -1e-8 for difference in diffs),
        'second_lower_error': sum(difference > 1e-8 for difference in diffs),
        'ties_within_1e_minus_8': sum(abs(difference) <= 1e-8 for difference in diffs),
        'mean_first_minus_second_error': sum(diffs) / len(diffs) if diffs else None,
    }
Path(sys.argv[2]).write_text(json.dumps(analysis, indent=2, allow_nan=False) + '\n')
print(json.dumps({key: value for key, value in analysis.items() if key not in {'families', 'matching_binding_pairs'}}, indent=2))
for family, value in analysis['families'].items():
    metric = value['responses_across_models']
    print(family, json.dumps({key: metric.get(key) for key in ['count', 'valid_count', 'accuracy', 'mean_score', 'mean_delta_e_ok', 'out_of_srgb_count']}))
