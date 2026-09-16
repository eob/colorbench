"""Descriptive paired analysis of an independently verified, sealed pilot run."""
import json
from collections import defaultdict
from pathlib import Path
import sys

from baseline.finalize import verify_finalization
from baseline.protocol import CHOICE_FAMILIES, NUMERIC_FAMILIES, NUMERIC_SCORING
from baseline.statistics import family_metrics


def _pair_counts(groups, first, second):
    pairs = [(group[first], group[second]) for group in groups if first in group and second in group]
    count = len(pairs)
    first_correct = sum(a['correct'] is True for a, _ in pairs)
    second_correct = sum(b['correct'] is True for _, b in pairs)
    return {
        'count': count,
        'unpaired_first_count': sum(first in group and second not in group for group in groups),
        'unpaired_second_count': sum(second in group and first not in group for group in groups),
        'both_correct': sum(a['correct'] is True and b['correct'] is True for a, b in pairs),
        'first_only_correct': sum(a['correct'] is True and b['correct'] is not True for a, b in pairs),
        'second_only_correct': sum(a['correct'] is not True and b['correct'] is True for a, b in pairs),
        'both_incorrect': sum(a['correct'] is not True and b['correct'] is not True for a, b in pairs),
        'first_invalid_count': sum(not a['valid'] for a, _ in pairs),
        'second_invalid_count': sum(not b['valid'] for _, b in pairs),
        'first_correct_count': first_correct,
        'second_correct_count': second_correct,
        'first_accuracy': first_correct / count if count else None,
        'second_accuracy': second_correct / count if count else None,
        'second_minus_first_accuracy': (second_correct - first_correct) / count if count else None,
    }


def _mapping_counts(groups):
    counts = _pair_counts(groups, 'sameA', 'sameB')
    valid = [(group['sameA'], group['sameB']) for group in groups if 'sameA' in group and 'sameB' in group
             and group['sameA']['valid'] and group['sameB']['valid']]
    consistent = sum((a['prediction']['choice'] == 'A') == (b['prediction']['choice'] == 'B') for a, b in valid)
    return {**counts, 'valid_pairs': len(valid), 'invalid_pairs': counts['count'] - len(valid),
            'semantic_consistent_pairs': consistent, 'semantic_inconsistent_pairs': len(valid) - consistent,
            'consistency_rate_among_valid_pairs': consistent / len(valid) if valid else None}


def _rgb_counts(rows):
    valid = [row for row in rows if row['valid']]
    largest = [max(row['component_errors'][channel] for channel in 'rgb') for row in valid]
    return {'response_count': len(rows), 'valid_count': len(valid), 'invalid_count': len(rows) - len(valid),
            'exact_count': sum(error == 0 for error in largest),
            'within_2_lsb_count': sum(error <= 2 for error in largest),
            'within_5_lsb_count': sum(error <= 5 for error in largest),
            'delta_e_hit_counts': {str(band): sum(row['within_bands'][str(band)] for row in valid)
                                   for band in NUMERIC_SCORING['exact_bands']}}


def analyze_report(report):
    rows = [dict(entry['result'], model_id=entry['model_id']) for entry in report['results'] if entry['included_in_comparison']]
    items = {item['task_id']: item for item in report['specimens']}
    model_ids = report['comparison']['model_ids']
    analysis = {
        'release': report['release'], 'run_id': report['run_id'], 'campaign': report['campaign'],
        'scope': ('Descriptive results on this fixed pilot; no independent-observation or population inference. '
                  'Colors, numeric targets, intervention conditions and answer mappings share correlated inputs. '
                  'Paired correctness includes invalid answers as incorrect; semantic consistency requires both answers valid. '
                  'RGB hit counts retain total and valid response counts.'),
        'model_count': len(model_ids), 'question_count': report['comparison']['count'],
        'group_count': len({items[task]['group_id'] for task in report['comparison']['task_ids']}),
        'families': {}, 'matching_binding_pairs': {}, 'numeric_format_pairs': {},
    }
    for family in CHOICE_FAMILIES + NUMERIC_FAMILIES:
        selected = [row for row in rows if row['family'] == family]
        overall = family_metrics(selected, family)
        models = []
        metric = 'accuracy' if family in CHOICE_FAMILIES else 'mean_score'
        for model in report['models']:
            if model['model_id'] in model_ids:
                models.append({'id': model['model_id'], 'name': model['model_config']['display_name'], **model['families'][family]})
        models.sort(key=lambda model: (model[metric] is None, -(model[metric] or 0), model['id']))
        slices = {}
        for dimension in ['difficulty', 'axis', 'layout', 'condition', 'same', 'direction', 'intendedSeparation']:
            values = sorted({items[row['task_id']]['design'].get(dimension) for row in selected},
                            key=lambda value: (value is None, str(value)))
            if dimension not in ('difficulty', 'axis') and len([value for value in values if value is not None]) < 2:
                continue
            slices[dimension] = {value: family_metrics([row for row in selected if items[row['task_id']]['design'].get(dimension) == value], family)
                                 for value in values}
        analysis['families'][family] = {'responses_across_models': overall, 'models': models, 'slices': slices}

    paired, conditions, mappings = defaultdict(dict), defaultdict(dict), defaultdict(dict)
    for row in rows:
        family, model, group = row['family'], row['model_id'], row['group_id']
        design = items[row['task_id']]['design']
        if family in ('matching', 'binding') + NUMERIC_FAMILIES:
            destination, label = paired[(model, group)], family
        elif family in ('context', 'smallmatch') and design.get('condition'):
            destination, label = conditions[(model, family, group)], design['condition']
        elif family == 'samediff' and design.get('mappingPairId'):
            destination, label = mappings[(model, design['mappingPairId'])], design['direction']
        else:
            continue
        if label in destination:
            raise ValueError(f'Duplicate paired family/condition for {model}: {row["task_id"]} ({label})')
        destination[label] = row

    for model in model_ids:
        groups = [value for (name, _), value in paired.items() if name == model]
        counts = _pair_counts(groups, 'matching', 'binding')
        analysis['matching_binding_pairs'][model] = {
            'count': counts['count'], 'both_correct': counts['both_correct'],
            'matching_only_correct': counts['first_only_correct'], 'binding_only_correct': counts['second_only_correct'],
            'both_incorrect': counts['both_incorrect'],
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

    comparisons = {'context': [('neutral', f'surround-{i}') for i in range(4)],
                   'smallmatch': [('filled-20', 'filled-84'), ('outline-3', 'outline-12')]}
    analysis['matched_condition_pairs'] = {}
    for family, comparisons_for_family in comparisons.items():
        analysis['matched_condition_pairs'][family] = {}
        selected = {key: group for key, group in conditions.items() if key[1] == family}
        for first, second in comparisons_for_family:
            analysis['matched_condition_pairs'][family][f'{first}_vs_{second}'] = {
                'first_condition': first, 'second_condition': second,
                'pooled': _pair_counts(list(selected.values()), first, second),
                'models': {model: _pair_counts([group for (name, _, _), group in selected.items() if name == model], first, second)
                           for model in model_ids},
            }
    analysis['same_different_mapping_pairs'] = {
        'first_mapping': 'sameA', 'second_mapping': 'sameB',
        'pooled': _mapping_counts(list(mappings.values())),
        'models': {model: _mapping_counts([group for (name, _), group in mappings.items() if name == model]) for model in model_ids},
    }
    analysis['hue_contexts'] = {}
    for context in ('fixed-lightness-chroma', 'varying-lightness-chroma'):
        selected = [row for row in rows if row['family'] == 'hue' and items[row['task_id']]['design'].get('difficulty') == context]
        analysis['hue_contexts'][context] = {
            'pooled': family_metrics(selected, 'hue'),
            'models': {model: family_metrics([row for row in selected if row['model_id'] == model], 'hue') for model in model_ids},
        }
    rgb = [row for row in rows if row['family'] == 'rgb']
    analysis['rgb_reconstruction'] = {
        'pooled': _rgb_counts(rgb),
        'models': {model: _rgb_counts([row for row in rgb if row['model_id'] == model]) for model in model_ids},
    }
    return analysis


def main():
    analysis = analyze_report(verify_finalization(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(analysis, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: analysis[key] for key in ('release', 'run_id', 'campaign', 'scope', 'model_count',
                                                   'question_count', 'group_count', 'numeric_format_pairs')}, indent=2))
    for family, value in analysis['families'].items():
        metric = value['responses_across_models']
        print(family, json.dumps({key: metric.get(key) for key in ['count', 'valid_count', 'accuracy', 'mean_score', 'mean_tight_score', 'mean_delta_e_ok', 'band_hit_rate', 'out_of_srgb_count']}))


if __name__ == '__main__':
    main()
