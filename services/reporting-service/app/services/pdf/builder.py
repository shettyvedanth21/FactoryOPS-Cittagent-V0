"""
FactoryOPS PDF Builder v5 - Single figure per page approach
Uses matplotlib subplots with GridSpec for pixel-perfect layout.
"""
from io import BytesIO
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import logging

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

logger = logging.getLogger(__name__)

CURRENCY = 'Rs.'
P = {
    'dark':    '#1e293b',
    'mid':     '#334155',
    'darkest': '#0f172a',
    'accent':  '#3b82f6',
    'green':   '#16a34a',
    'amber':   '#d97706',
    'red':     '#dc2626',
    'grey':    '#f8fafc',
    'border':  '#e2e8f0',
    'text':    '#1e293b',
    'tmid':    '#64748b',
    'tlight':  '#94a3b8',
    'white':   '#ffffff',
    'lblue':   '#eff6ff',
    'lgreen':  '#f0fdf4',
}

A4_W = 8.27
A4_H = 11.69


def _make_page():
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.patch.set_facecolor(P['white'])
    return fig


def _add_ax(fig, left, bottom, width, height):
    """All coords in inches, converted to figure fractions."""
    return fig.add_axes([
        left   / A4_W,
        bottom / A4_H,
        width  / A4_W,
        height / A4_H
    ])


def _filled_ax(fig, left, bottom, width, height, color):
    """Add a solid-color rectangle axes."""
    ax = _add_ax(fig, left, bottom, width, height)
    ax.set_facecolor(color)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    return ax


def draw_header(fig, title, subtitle, period, report_id,
                margin=0.55, top=11.15, cw=7.17):
    """
    Draw 4-layer header. Returns y position below header.
    All coords in inches from bottom of page.
    """
    # Layer heights
    brand_h  = 0.26
    title_h  = 0.60
    accent_h = 0.055
    sub_h    = 0.30

    y = top  # start from top, go down

    # Brand bar
    y -= brand_h
    ax = _filled_ax(fig, margin, y, cw, brand_h, P['mid'])
    ax.text(0.01, 0.5, 'FactoryOPS  |  Energy Intelligence Platform',
            transform=ax.transAxes, va='center',
            fontsize=8, color=P['tlight'])
    ax.text(0.99, 0.5, f'Report ID: {str(report_id)[:8]}...',
            transform=ax.transAxes, va='center', ha='right',
            fontsize=7.5, color=P['tlight'])

    # Title bar
    y -= title_h
    ax = _filled_ax(fig, margin, y, cw, title_h, P['dark'])
    ax.text(0.02, 0.5, title,
            transform=ax.transAxes, va='center',
            fontsize=22, color=P['white'], fontweight='bold')

    # Accent line
    y -= accent_h
    _filled_ax(fig, margin, y, cw, accent_h, P['accent'])

    # Subtitle bar
    y -= sub_h
    ax = _filled_ax(fig, margin, y, cw, sub_h, P['darkest'])
    ax.text(0.02, 0.5, subtitle,
            transform=ax.transAxes, va='center',
            fontsize=9.5, color=P['tmid'])
    ax.text(0.98, 0.5, f'Period: {period}',
            transform=ax.transAxes, va='center', ha='right',
            fontsize=9.5, color=P['tmid'])

    return y  # bottom of header


def draw_section(fig, text, y, margin=0.55, cw=7.17):
    """Draw section heading. Returns new y."""
    h = 0.30
    y -= h
    ax = _filled_ax(fig, margin, y, cw, h, P['white'])
    # blue line at top
    ax.axhline(y=0.88, color=P['accent'], linewidth=1.8, zorder=2)
    ax.text(0.0, 0.30, text,
            transform=ax.transAxes, va='center',
            fontsize=11.5, color=P['dark'], fontweight='bold')
    return y


def draw_kpi_cards(fig, cards, y, margin=0.55, cw=7.17):
    """
    Draw 4 KPI cards. Returns new y.
    cards = [(label, value, unit, color), ...]
    """
    n = len(cards)
    gap = 0.10
    card_w = (cw - gap * (n - 1)) / n
    card_h = 1.10

    y -= card_h

    for i, (label, value, unit, color) in enumerate(cards):
        x = margin + i * (card_w + gap)

        # Card background
        ax = _filled_ax(fig, x, y, card_w, card_h, P['white'])

        # Draw border manually
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(P['border'])
            spine.set_linewidth(0.8)

        # Top accent bar — drawn as a patch inside the axes
        ax.add_patch(mpatches.Rectangle(
            (0, 0.895), 1, 0.105,
            facecolor=color,
            transform=ax.transAxes,
            clip_on=True,
            zorder=5
        ))

        # Label
        ax.text(0.5, 0.75, label,
                transform=ax.transAxes,
                ha='center', va='center',
                fontsize=7.5, color=P['tlight'],
                zorder=6)

        # Value
        vlen = len(str(value))
        fs = 17 if vlen < 10 else (14 if vlen < 14 else 11)
        ax.text(0.5, 0.46, str(value),
                transform=ax.transAxes,
                ha='center', va='center',
                fontsize=fs, color=color,
                fontweight='bold', zorder=6)

        # Unit
        ax.text(0.5, 0.17, unit,
                transform=ax.transAxes,
                ha='center', va='center',
                fontsize=8, color=P['tmid'],
                zorder=6)

    return y - 0.15


def draw_table(fig, headers, rows, col_fracs, y,
               margin=0.55, cw=7.17,
               row_h=0.27, total_row=False):
    """Draw a table. Returns new y."""
    all_rows = [headers] + rows
    table_h = len(all_rows) * row_h
    y_start = y

    for ri, row in enumerate(all_rows):
        is_header = ri == 0
        is_total = total_row and ri == len(all_rows) - 1
        if is_header:
            bg = P['dark']
            tc = P['white']
            fw = 'bold'
        elif is_total:
            bg = P['lblue']
            tc = P['text']
            fw = 'bold'
        else:
            bg = P['grey'] if ri % 2 == 0 else P['white']
            tc = P['text']
            fw = 'normal'

        row_y = y_start - (ri + 1) * row_h

        x = margin
        for ci, (cell, frac) in enumerate(zip(row, col_fracs)):
            cell_w = cw * frac
            ax = _filled_ax(fig, x, row_y, cell_w, row_h, bg)

            # bottom border
            ax.axhline(y=0, color=P['border'], linewidth=0.5)

            # accent underline on header
            if is_header:
                ax.axhline(y=0, color=P['accent'], linewidth=1.8)

            # top border on total row
            if is_total:
                ax.axhline(y=1, color=P['accent'], linewidth=1.5)

            ha = 'left' if ci == 0 else 'center'
            tx = 0.05 if ci == 0 else 0.5

            ax.text(tx, 0.5, str(cell),
                    transform=ax.transAxes,
                    ha=ha, va='center',
                    fontsize=8.5, color=tc,
                    fontweight=fw)
            x += cell_w

    y = y_start - table_h
    return y


def draw_bar_chart(fig, pairs, title, y,
                   margin=0.55, cw=7.17, chart_h=2.5):
    """Draw bar chart. Returns new y."""
    if not pairs:
        return y

    pairs = pairs[:31]
    labels = [str(l)[-5:] for l, _ in pairs]
    values = [max(0.0, float(v)) for _, v in pairs]

    y -= chart_h
    ax = _add_ax(fig, margin, y, cw, chart_h)
    ax.set_facecolor(P['grey'])
    fig_bg = fig.get_facecolor()

    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=P['accent'],
                  width=0.6, edgecolor='none', zorder=3)

    if max(values) > 0:
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(values) * 0.02,
                    f'{val:,.0f}',
                    ha='center', va='bottom',
                    fontsize=max(5.5, 8.5 - len(labels) // 5),
                    color=P['dark'], fontweight='bold'
                )

    angle = 40 if len(labels) > 6 else 0
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=angle,
                       ha='right' if angle else 'center',
                       fontsize=8, color=P['tmid'])
    ax.set_ylabel('kWh', fontsize=8.5, color=P['tmid'])
    ax.set_title(title, fontsize=11, fontweight='bold',
                 color=P['dark'], pad=10)
    ax.tick_params(axis='y', labelsize=8, colors=P['tmid'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(P['border'])
    ax.spines['bottom'].set_color(P['border'])
    ax.yaxis.grid(True, color=P['border'], linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(-0.6, len(labels) - 0.4)

    return y - 0.15


def draw_insights(fig, items, y, margin=0.55, cw=7.17,
                  bg=None, border=None):
    """Draw insights box. Returns new y."""
    if not items:
        return y
    bg = bg or P['lblue']
    border = border or P['accent']

    line_h = 0.28
    box_h = len(items) * line_h + 0.18
    y -= box_h

    ax = _filled_ax(fig, margin, y, cw, box_h, bg)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(border)
        spine.set_linewidth(0.7)

    # left accent bar
    ax.add_patch(mpatches.Rectangle(
        (0, 0), 0.007, 1,
        facecolor=border,
        transform=ax.transAxes,
        clip_on=True, zorder=3
    ))

    for i, item in enumerate(items):
        frac = 1.0 - (0.12 + i * line_h / box_h + line_h / box_h / 2)
        ax.text(0.022, frac, f'\u25cf  {item}',
                transform=ax.transAxes,
                va='center', fontsize=8.5,
                color=P['text'], zorder=4)

    return y - 0.12


def draw_note(fig, text, y, margin=0.55, cw=7.17):
    """Draw small italic note. Returns new y."""
    h = 0.22
    y -= h
    ax = _filled_ax(fig, margin, y, cw, h, P['white'])
    ax.text(0.0, 0.5, text,
            transform=ax.transAxes,
            fontsize=7, color=P['tlight'],
            style='italic', va='center')
    return y - 0.06


def draw_footer(fig, page_num, margin=0.55, cw=7.17):
    """Draw footer at bottom of page."""
    h = 0.22
    ax = _filled_ax(fig, margin, 0.30, cw, h, P['white'])
    ax.axhline(y=0.92, color=P['border'], linewidth=0.8)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    ax.text(0.0, 0.35,
            'Generated by FactoryOPS Energy Intelligence Platform',
            transform=ax.transAxes,
            fontsize=7, color=P['tlight'], va='center')
    ax.text(1.0, 0.35, f'{ts}  |  Page {page_num}',
            transform=ax.transAxes,
            fontsize=7, color=P['tlight'],
            va='center', ha='right')


class PDFBuilder:

    MARGIN = 0.55
    TOP    = 11.15
    CW     = 7.17  # A4_W - 2*MARGIN = 8.27 - 1.10

    def _new_page(self, pdf, page_num):
        fig = _make_page()
        draw_footer(fig, page_num,
                    margin=self.MARGIN, cw=self.CW)
        return fig

    def _save_page(self, pdf, fig):
        pdf.savefig(fig, bbox_inches=None)
        plt.close(fig)

    def build_consumption_report(
        self,
        data: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> bytes:
        devices     = data.get('devices', [])
        report_id   = data.get('report_id', 'N/A')
        tariff_rate = float(data.get('tariff_rate', 8.5))
        daily       = data.get('daily_breakdown', [])

        total_kwh   = sum(d.get('total_kwh',    0) for d in devices)
        total_peak  = max((d.get('peak_power_w', 0) for d in devices), default=0)
        total_hours = sum(d.get('running_hours', 0) for d in devices)
        total_cost  = total_kwh * tariff_rate

        device_label = ', '.join(
            d.get('device_name', d.get('device_id', ''))
            for d in devices
        ) or f'{len(devices)} device(s)'

        buf = BytesIO()
        with PdfPages(buf) as pdf:
            page = 1
            fig = self._new_page(pdf, page)
            M, T, CW = self.MARGIN, self.TOP, self.CW

            # ── Header ──────────────────────────────────────────────────────
            y = draw_header(fig,
                'Energy Consumption Report',
                device_label,
                f'{start_date} to {end_date}',
                report_id, M, T, CW)
            y -= 0.18

            # ── Executive Summary ────────────────────────────────────────────
            y = draw_section(fig, 'Executive Summary', y, M, CW)
            y -= 0.08
            y = draw_kpi_cards(fig, [
                ('TOTAL ENERGY',
                 f'{total_kwh:,.1f}', 'kWh', P['accent']),
                ('PEAK DEMAND',
                 f'{total_peak:,.1f}', 'Watts', P['amber']),
                ('RUNNING HOURS',
                 f'{total_hours:,.1f}', 'hrs', P['green']),
                ('EST. COST',
                 f'{CURRENCY} {total_cost:,.0f}', 'INR', P['red']),
            ], y, M, CW)
            y -= 0.10

            # ── Device Breakdown ─────────────────────────────────────────────
            y = draw_section(fig, 'Device Breakdown', y, M, CW)
            y -= 0.05
            dev_rows = []
            for d in devices:
                c = d.get('total_kwh', 0) * tariff_rate
                dev_rows.append([
                    d.get('device_name', d.get('device_id', '')),
                    d.get('device_id', ''),
                    f"{d.get('total_kwh', 0):,.1f}",
                    f"{d.get('peak_power_w', 0):,.1f}",
                    f"{d.get('running_hours', 0):.1f}",
                    f"{CURRENCY} {c:,.0f}",
                ])
            y = draw_table(fig,
                ['Device Name','Device ID','kWh','Peak(W)','Hrs','Cost'],
                dev_rows,
                [0.26, 0.19, 0.15, 0.14, 0.10, 0.16],
                y, M, CW)
            y -= 0.10

            # ── Daily Chart ──────────────────────────────────────────────────
            pairs = [
                (e.get('date', ''), float(e.get('kwh', 0)))
                for e in daily
                if float(e.get('kwh', 0)) > 0
            ]
            y = draw_section(fig, 'Daily Energy Consumption', y, M, CW)
            y -= 0.05
            if pairs:
                chart_h = min(2.5, max(1.5, y - 1.8))
                y = draw_bar_chart(fig, pairs,
                    'Daily kWh Consumption', y, M, CW, chart_h)
            else:
                y = draw_note(fig,
                    'No daily data yet — accumulates after multiple days of operation.',
                    y, M, CW)
            y -= 0.10

            # ── Check space — new page if needed ─────────────────────────────
            if y < 2.5:
                self._save_page(pdf, fig)
                page += 1
                fig = self._new_page(pdf, page)
                y = self.TOP - 0.30
                M, CW = self.MARGIN, self.CW

            # ── Cost Estimation ──────────────────────────────────────────────
            y = draw_section(fig, 'Cost Estimation', y, M, CW)
            y -= 0.05
            cost_rows = []
            for d in devices:
                c = d.get('total_kwh', 0) * tariff_rate
                cost_rows.append([
                    d.get('device_name', d.get('device_id', '')),
                    d.get('device_id', ''),
                    f"{d.get('total_kwh', 0):,.2f} kWh",
                    f"{CURRENCY} {c:,.2f}",
                ])
            cost_rows.append([
                '', 'TOTAL',
                f'{total_kwh:,.2f} kWh',
                f'{CURRENCY} {total_cost:,.2f}',
            ])
            y = draw_table(fig,
                ['Device Name','Device ID','Energy','Cost (INR)'],
                cost_rows,
                [0.30, 0.22, 0.24, 0.24],
                y, M, CW, total_row=True)
            y = draw_note(fig,
                f'* Tariff: {CURRENCY} {tariff_rate}/kWh '
                f'(Default — configure in Settings > Tariffs)',
                y, M, CW)
            y -= 0.10

            # ── Key Insights ─────────────────────────────────────────────────
            y = draw_section(fig, 'Key Insights', y, M, CW)
            y -= 0.05
            insights = []
            for d in devices:
                name = d.get('device_name', d.get('device_id', ''))
                kwh  = d.get('total_kwh', 0)
                hrs  = d.get('running_hours', 0)
                cost = kwh * tariff_rate
                avg  = kwh / hrs if hrs > 0 else 0
                insights.append(
                    f'{name}: {kwh:,.1f} kWh over {hrs:.0f} hrs '
                    f'(avg {avg:.1f} kWh/hr) — cost {CURRENCY} {cost:,.2f}'
                )
            if total_peak > 0:
                insights.append(
                    f'Peak demand: {total_peak:,.1f} W across '
                    f'{len(devices)} device(s)'
                )
            insights.append(
                f'Total: {CURRENCY} {total_cost:,.2f} at '
                f'{CURRENCY} {tariff_rate}/kWh — '
                f'configure tariffs in Settings for precise billing'
            )
            draw_insights(fig, insights, y, M, CW)

            self._save_page(pdf, fig)

        buf.seek(0)
        return buf.read()

    def build_wastage_report(self, data: Dict[str, Any]) -> bytes:
        summary   = data.get('summary', {})
        period    = data.get('period', {})
        start     = str(period.get('start_date', ''))[:10]
        end       = str(period.get('end_date',   ''))[:10]
        report_id = data.get('report_id', 'N/A')
        breakdown = data.get('breakdown', [])
        dev_list  = data.get('devices', [])
        recs      = data.get('recommendations', [])

        buf = BytesIO()
        with PdfPages(buf) as pdf:
            page = 1
            fig = self._new_page(pdf, page)
            M, T, CW = self.MARGIN, self.TOP, self.CW

            y = draw_header(fig,
                'Energy Wastage Report',
                'Wastage & Efficiency Analysis',
                f'{start} to {end}',
                report_id, M, T, CW)
            y -= 0.18

            eff   = float(summary.get('efficiency_score', 0))
            eff_c = (P['green'] if eff >= 85
                     else P['amber'] if eff >= 70 else P['red'])

            y = draw_section(fig, 'Summary', y, M, CW)
            y -= 0.08
            y = draw_kpi_cards(fig, [
                ('TOTAL WASTED',
                 f"{summary.get('total_wasted_kwh',0):,.1f}",
                 'kWh', P['red']),
                ('COST IMPACT',
                 f"{CURRENCY} {summary.get('total_wasted_rupees',0):,.0f}",
                 'INR', P['amber']),
                ('EFFICIENCY',
                 f"{eff:.1f}%",
                 summary.get('efficiency_grade','N/A'), eff_c),
                ('IDLE HOURS',
                 f"{summary.get('idle_hours',0):.1f}",
                 'hrs', P['mid']),
            ], y, M, CW)
            y -= 0.10

            if breakdown:
                y = draw_section(fig, 'Wastage Breakdown', y, M, CW)
                y -= 0.05
                b_rows = [[
                    bk.get('source', ''),
                    f"{bk.get('kwh', 0):,.2f}",
                    f"{bk.get('percent', 0):.1f}%"
                ] for bk in breakdown]
                y = draw_table(fig,
                    ['Source','Wasted (kWh)','Share (%)'],
                    b_rows, [0.50, 0.25, 0.25],
                    y, M, CW)
                y -= 0.10

            if dev_list:
                y = draw_section(fig, 'Device Efficiency', y, M, CW)
                y -= 0.05
                d_rows = [[
                    d.get('device_name', d.get('device_id','')),
                    d.get('device_id',''),
                    f"{d.get('wasted_kwh',0):,.1f}",
                    f"{d.get('efficiency_score',0):.1f}%",
                    d.get('efficiency_grade','N/A')
                ] for d in dev_list]
                y = draw_table(fig,
                    ['Device Name','Device ID',
                     'Wasted kWh','Efficiency','Grade'],
                    d_rows,
                    [0.27,0.22,0.18,0.17,0.16],
                    y, M, CW)
                y -= 0.10

            if recs:
                y = draw_section(fig, 'Recommendations', y, M, CW)
                y -= 0.05
                rec_items = [
                    f"{r.get('rank',i+1)}. {r.get('action','')} — "
                    f"Save {r.get('potential_savings_kwh',0):.1f} kWh "
                    f"/ {CURRENCY} {r.get('potential_savings_rupees',0):,.0f}"
                    for i, r in enumerate(recs)
                ]
                y = draw_insights(fig, rec_items, y, M, CW,
                                  bg=P['lgreen'], border=P['green'])

            draw_note(fig,
                f'* Costs use {CURRENCY} 8.5/kWh default tariff.',
                y, M, CW)

            self._save_page(pdf, fig)

        buf.seek(0)
        return buf.read()


pdf_builder = PDFBuilder()
