"""Compare local kernels to the original commit; excludes plotting and imports.

Run: python benchmark_optimizations.py
Only run against this trusted repository: the baseline Python is executed.
"""

import json
import argparse
import platform
import subprocess
import sys
import timeit
import tracemalloc
import types
import tempfile
from pathlib import Path

import surface_code_challenge as new
from gf2 import binary_rank
from qec_checkpoints import _toric_matrices

BASELINE = '938063c07bafcc15a182d94bd74a181db9495cbf'


def load_baseline(name, filename, revision=BASELINE):
    source = subprocess.check_output(['git', 'show', f'{revision}:{filename}'])
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, filename, 'exec'), module.__dict__)
    return module


def stats(fn, number):
    seconds = min(timeit.repeat(fn, number=number, repeat=5)) / number
    tracemalloc.start()
    fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {'milliseconds': round(seconds * 1000, 4), 'python_peak_bytes': peak}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default=BASELINE,
                        help='Trusted local Git revision to compare against')
    parser.add_argument('--output', type=Path,
                        default=Path('challenge_results/optimization_benchmarks.json'))
    args = parser.parse_args()
    old = load_baseline('baseline_challenge', 'surface_code_challenge.py', args.baseline)
    lab = load_baseline('baseline_lab', 'lab4_util.py', args.baseline)
    patches = {'A': (0, 0), 'B': (59, 59)}
    patches.update({f'P{i}': (1 + i % 58, 1 + i // 58) for i in range(500)})
    before = old.Layout('large', 60, 60, patches)
    after = new.Layout('large', 60, 60, patches)
    op = new.Measurement('route', 'A', 'B', 'Z')
    assert old.route(before, op) == new.route(after, op)
    chain = tuple(new.Measurement(str(i), 'A', 'B', 'Z',
                                  (str(i-1),) if i else ()) for i in range(1000))
    small = new.Layout('chain', 3, 3, {'A': (0, 0), 'B': (0, 2)})
    assert old.schedule(small, chain) == new.schedule(small, chain)
    contended = tuple(new.Measurement(str(i), 'A', 'B', 'Z') for i in range(300))
    chain_steps = new.schedule(small, chain)
    for layout in new.LAYOUTS:
        assert old.schedule(layout) == new.schedule(layout)
    assert old.schedule(small, contended) == new.schedule(small, contended)
    matrix = _toric_matrices()[0]
    assert lab.matrixRank(matrix) == binary_rank(matrix)
    cases = {
        'route_60x60_502_patches': (lambda: old.route(before, op),
                                  lambda: new.route(after, op), 10),
        'chain_1000_operations': (lambda: old.schedule(small, chain),
                                 lambda: new.schedule(small, chain), 1),
        'rank_toric_72x144': (lambda: lab.matrixRank(matrix),
                             lambda: binary_rank(matrix), 10),
        'route_single_tile': (lambda: old.route(small, op),
                              lambda: new.route(small, op), 1000),
        'schedule_compact': (lambda: old.schedule(new.LAYOUTS[0]),
                             lambda: new.schedule(new.LAYOUTS[0]), 100),
        'schedule_workload_aligned': (lambda: old.schedule(new.LAYOUTS[-1]),
                                      lambda: new.schedule(new.LAYOUTS[-1]), 100),
        'contended_300_operations': (lambda: old.schedule(small, contended),
                                     lambda: new.schedule(small, contended), 2),
        'validate_chain_1000': (lambda: old.validate_schedule(small, chain_steps, chain),
                                lambda: new.validate_schedule(small, chain_steps, chain), 5),
    }
    results = {name: {'before': stats(a, number), 'after': stats(b, number)}
               for name, (a, b, number) in cases.items()}
    # Include an actual PNG render/save. Warm both paths before measuring.
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory) / 'schedule.png'
        drawing = new.Layout('render', 24, 24, {'A': (0, 0), 'B': (0, 2)})
        drawing_steps = new.schedule(drawing, (new.WORKLOAD[0],))
        def render(module):
            module.draw_schedule(drawing, drawing_steps, destination)
        render(old)
        render(new)
        results['render_24x24_png'] = {
            'before': stats(lambda: render(old), 1),
            'after': stats(lambda: render(new), 1),
        }
    payload = {'baseline_commit': args.baseline, 'python': platform.python_version(),
               'method': 'Best of 5 timing repeats; tracemalloc peak separately; '
                         'excludes imports, fixture creation and native memory. '
                         'Rendering measured separately, including PNG saving.',
               'results': results}
    output = args.output
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
