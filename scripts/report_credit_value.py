"""Generate a plain-text report summarising credit ledger value."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator import metrics as metrics_module


def _format_seconds(value: float) -> str:
    return f"{value:.0f}s"


def _build_seconds_section(window_stats: dict[int, dict[str, object]]) -> str:
    lines = ["## Seconds saved distribution", ""]
    lines.append("| Window | Events | Total | Avg | P50 | P90 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for days, payload in sorted(window_stats.items()):
        lines.append(
            "| {window}d | {count} | {total} | {mean} | {p50} | {p90} |".format(
                window=days,
                count=int(float(payload.get("count", 0))),
                total=_format_seconds(float(payload.get("totalSeconds", 0.0))),
                mean=_format_seconds(float(payload.get("avgSeconds", payload.get("meanSeconds", 0.0)))),
                p50=_format_seconds(float(payload.get("p50Seconds", 0.0))),
                p90=_format_seconds(float(payload.get("p90Seconds", 0.0))),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _build_percentile_chart(window_stats: dict[int, dict[str, object]]) -> str:
    if not window_stats:
        return ""
    max_value = max(float(stats.get("p90Seconds", 0.0)) for stats in window_stats.values()) or 1.0
    width = 24
    lines = ["```", "Window  p50                          p90"]
    for days, payload in sorted(window_stats.items()):
        p50 = float(payload.get("p50Seconds", 0.0))
        p90 = float(payload.get("p90Seconds", 0.0))
        p50_bar = "#" * max(0, int((p50 / max_value) * width))
        p90_bar = "#" * max(0, int((p90 / max_value) * width))
        lines.append(
            f"{days:>3}d   {p50_bar:<{width}} {p50:>4.0f}s   {p90_bar:<{width}} {p90:>4.0f}s"
        )
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _build_baseline_section(baseline: dict[str, object]) -> str:
    lines = ["## Baseline vs with-apply", ""]
    base = baseline.get("baseline", {}) if isinstance(baseline, dict) else {}
    applied = baseline.get("withApply", {}) if isinstance(baseline, dict) else {}
    lines.append("| Metric | Baseline mean | Baseline p90 | With apply mean | With apply p90 |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for metric in ("ttr", "frt"):
        base_stats = base.get(metric, {}) if isinstance(base, dict) else {}
        apply_stats = applied.get(metric, {}) if isinstance(applied, dict) else {}
        lines.append(
            "| {metric} | {base_mean} | {base_p90} | {apply_mean} | {apply_p90} |".format(
                metric=metric.upper(),
                base_mean=_format_seconds(float(base_stats.get("meanSeconds", 0.0))),
                base_p90=_format_seconds(float(base_stats.get("p90Seconds", 0.0))),
                apply_mean=_format_seconds(float(apply_stats.get("meanSeconds", 0.0))),
                apply_p90=_format_seconds(float(apply_stats.get("p90Seconds", 0.0))),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _build_top_contributors(contributors: list[dict[str, object]], window_days: int) -> str:
    lines = [f"## Top contributors (last {window_days} days)", ""]
    if not contributors:
        lines.append("No credit events in the selected window.")
        lines.append("")
        return "\n".join(lines)
    lines.append("| Actor | Seconds saved | Events | Share |")
    lines.append("| --- | ---: | ---: | ---: |")
    for item in contributors[:10]:
        seconds = float(item.get("secondsSaved", 0.0))
        lines.append(
            "| {actor} | {seconds} | {events} | {share:.1%} |".format(
                actor=item.get("id", "?"),
                seconds=_format_seconds(seconds),
                events=int(item.get("events", 0)),
                share=float(item.get("share", 0.0)),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _build_throughput_section(stats: dict[str, object]) -> str:
    window = int(float(stats.get("windowDays", 0))) if stats else 0
    count = int(float(stats.get("count", 0))) if stats else 0
    rate = float(stats.get("appliesPerDay", 0.0)) if stats else 0.0
    lines = [f"## Apply throughput (last {window} days)", ""]
    lines.append(f"Total applies: **{count}**")
    lines.append(f"Per-day rate: **{rate:.2f}**")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate credit value report")
    parser.add_argument(
        "--out",
        default="artifacts/credit_report.md",
        help="Destination markdown file",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Rolling window (days) for the top contributors section",
    )
    args = parser.parse_args(argv)

    window_days = sorted({7, 30, args.window})
    window_stats = {days: metrics_module.seconds_saved_window(days) for days in window_days}
    baseline = metrics_module.ttr_frt_baseline()
    contributors = metrics_module.top_contributors(window_days=args.window)
    throughput_stats = metrics_module.throughput(window_days=7)

    report_lines = ["# Credit value report", ""]
    report_lines.append(_build_seconds_section(window_stats))
    report_lines.append(_build_percentile_chart(window_stats))
    report_lines.append(_build_baseline_section(baseline))
    report_lines.append(_build_top_contributors(contributors, args.window))
    report_lines.append(_build_throughput_section(throughput_stats))

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Report written to {output_path}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
