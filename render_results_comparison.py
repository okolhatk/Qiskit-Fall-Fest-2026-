"""Create a slide-ready comparison from the validated saved experiment results."""

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from surface_code_challenge import LAYOUTS, validate_schedule


def main():
    output = Path(__file__).parent / 'challenge_results'
    data = json.loads((output / 'results.json').read_text(encoding='utf-8'))
    bg, fg, muted = '#193f43', '#ffffff', '#bed2d2'
    teal, orange, yellow = '#a8dadc', '#f4b183', '#ffe7a0'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(16, 9), facecolor=bg)
    fig.text(.5, .945, 'Same workload. Better placement.', ha='center',
             color=fg, fontsize=29, weight='bold')
    fig.text(.5, .897, 'ZZ on AB and CD, then XX on BC and AD',
             ha='center', color=muted, fontsize=16)
    labels = ['COMPACT', 'SPACIOUS', 'WORKLOAD-ALIGNED']
    insights = ['Shared workspace; more waiting',
                'More space buys one fewer step',
                'Placement enables both pairs to run together']
    for i, layout in enumerate(LAYOUTS):
        left, width = .04 + .32*i, .28
        center = left + width/2
        steps = data['schedules'][layout.name]
        validate_schedule(layout, steps)
        summary = next(r for r in data['comparison'] if r['layout'] == layout.name)
        assert summary['tiles'] == layout.area
        assert summary['time_steps'] == len(steps)
        assert summary['tile_steps'] == layout.area * len(steps)
        accent = teal if i == 2 else fg
        fig.text(center, .833, labels[i], ha='center', color=accent,
                 fontsize=20, weight='bold')
        fig.text(center, .795, insights[i], ha='center', color=muted, fontsize=12)
        ax = fig.add_axes([left, .475, width, .30], facecolor=bg)
        # Shared limits preserve identical tile scale across the three boards.
        ox, oy = (7-layout.width)/2, (5-layout.height)/2
        for x in range(layout.width):
            for y in range(layout.height):
                ax.add_patch(Rectangle((x+ox, y+oy), 1, 1, facecolor='white',
                                       edgecolor='#c9d3d3', linewidth=.8))
        for item, color in zip(steps[0], [teal, orange]):
            for x, y in item['path']:
                ax.add_patch(Rectangle((x+ox, y+oy), 1, 1, facecolor=color,
                                       edgecolor='#729393', linewidth=.8))
        for label, (x, y) in layout.patches.items():
            x, y = x+ox, y+oy
            ax.add_patch(Rectangle((x, y), 1, 1, facecolor=yellow, edgecolor='none'))
            ax.text(x+.5, y+.5, label, ha='center', va='center',
                    fontsize=16, weight='bold', color='#132c30')
            for yy in (y, y+1):
                ax.plot([x, x+1], [yy, yy], color='#132c30', linewidth=2)
            for xx in (x, x+1):
                ax.plot([xx, xx], [y, y+1], color='#132c30', linewidth=2,
                        linestyle=':')
        ax.set(xlim=(-.3, 7.3), ylim=(5.3, -.3), aspect='equal')
        ax.axis('off')
        fig.text(center, .445, f'{layout.area} tiles  ×  {len(steps)} steps',
                 color=fg, fontsize=19, ha='center')
        fig.text(center, .392, f"{summary['tile_steps']} tile-steps", color=accent,
                 fontsize=28, weight='bold', ha='center')
        fig.text(left, .338, 'FULL SCHEDULE', color=muted, fontsize=10, weight='bold')
        # Same slot width everywhere: fewer slots means less elapsed time.
        slot = width/4
        for index, step in enumerate(steps):
            x = left + index*slot
            fig.add_artist(Rectangle((x, .23), slot-.006, .09,
                           transform=fig.transFigure, facecolor='#28565b',
                           edgecolor='#628488', linewidth=.8))
            fig.text(x+(slot-.006)/2, .297, f'Step {index+1}', ha='center',
                     color=muted, fontsize=10)
            text = '\n'.join(item['operation'].replace('_', ' ') for item in step)
            fig.text(x+(slot-.006)/2, .263, text, ha='center', va='center',
                     color=fg, fontsize=11, linespacing=1.5)
    for x in [.34, .66]:
        fig.add_artist(plt.Line2D([x, x], [.23, .85], transform=fig.transFigure,
                                 color='#527477', linewidth=.8))
    fig.text(.5, .168, '40% less area     •     50% fewer steps     •     70% fewer tile-steps',
             ha='center', color=teal, fontsize=21, weight='bold')
    fig.text(.5, .125, 'Workload-aligned vs. original compact — under the same restricted tile model',
             ha='center', color=fg, fontsize=13)
    fig.text(.5, .073, 'Boards show step 1 at the same tile scale; timelines show the complete workload.',
             ha='center', color=muted, fontsize=11)
    fig.text(.5, .043, 'Yellow: data patches   |   Teal/orange: auxiliary paths   |   White: idle tiles (counted)',
             ha='center', color=muted, fontsize=11)
    for suffix in ['png', 'svg']:
        path = output / f'results_insight_comparison.{suffix}'
        fig.savefig(path, dpi=200, facecolor=bg)
        print(path)
    plt.close(fig)


if __name__ == '__main__':
    main()
