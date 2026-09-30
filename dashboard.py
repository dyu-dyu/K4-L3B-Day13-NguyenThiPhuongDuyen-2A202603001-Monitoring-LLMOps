from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


LOG_PATH = Path(__file__).resolve().parent / "data" / "logs.jsonl"
TIME_RANGE_MINUTES = 60
REFRESH_SECONDS = 30


def load_logs(path: Path = LOG_PATH) -> pd.DataFrame:
    records: list[dict] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)

    frame = pd.DataFrame(records)
    if "ts" not in frame.columns:
        return pd.DataFrame()

    frame["ts"] = pd.to_datetime(frame["ts"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["ts"])
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=TIME_RANGE_MINUTES)
    return frame.loc[frame["ts"] >= cutoff].sort_values("ts")


def numeric(frame: pd.DataFrame, field: str) -> pd.Series:
    if field not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[field], errors="coerce").dropna()


def percentile(series: pd.Series, value: float) -> float:
    return float(series.quantile(value)) if not series.empty else 0.0


def metric_line_chart(
    frame: pd.DataFrame,
    *,
    x: str,
    fields: list[str],
    unit: str,
    threshold: float,
) -> None:
    available = [field for field in fields if field in frame.columns]
    if frame.empty or not available:
        st.info("Chưa có dữ liệu trong cửa sổ thời gian hiện tại.")
        return

    chart_data = frame[[x, *available]].melt(
        id_vars=[x], var_name="metric", value_name="value"
    )
    chart_data["value"] = pd.to_numeric(chart_data["value"], errors="coerce")
    chart_data = chart_data.dropna(subset=["value"])

    lines = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{x}:T", title="Time"),
            y=alt.Y("value:Q", title=unit),
            color=alt.Color("metric:N", title="Metric"),
            tooltip=[
                alt.Tooltip(f"{x}:T", title="Time"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format=".4f"),
            ],
        )
    )
    threshold_rule = (
        alt.Chart(pd.DataFrame({"threshold": [threshold]}))
        .mark_rule(color="#ef4444", strokeDash=[6, 4])
        .encode(y="threshold:Q")
    )
    st.altair_chart(lines + threshold_rule, width="stretch")


def response_events(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "event" not in frame.columns:
        return pd.DataFrame()
    return frame.loc[frame["event"] == "response_sent"].copy()


def request_events(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "event" not in frame.columns:
        return pd.DataFrame()
    return frame.loc[frame["event"] == "request_received"].copy()


def render_latency(frame: pd.DataFrame) -> None:
    responses = response_events(frame)
    latency = numeric(responses, "latency_ms")
    ttft = numeric(responses, "ttft_ms")

    st.subheader("1. Latency percentiles and TTFT")
    columns = st.columns(4)
    columns[0].metric("Latency P50", f"{percentile(latency, 0.50):.0f} ms")
    columns[1].metric("Latency P95", f"{percentile(latency, 0.95):.0f} ms")
    columns[2].metric("Latency P99", f"{percentile(latency, 0.99):.0f} ms")
    columns[3].metric("TTFT P95", f"{percentile(ttft, 0.95):.0f} ms")
    st.caption("Threshold: latency P95 ≤ 3000 ms")
    metric_line_chart(
        responses,
        x="ts",
        fields=["latency_ms", "ttft_ms"],
        unit="milliseconds",
        threshold=3000,
    )


def render_traffic(frame: pd.DataFrame) -> None:
    requests = request_events(frame)
    st.subheader("2. Request traffic")
    st.metric("Requests in last 60 minutes", len(requests), help="Unit: requests")
    st.caption("Threshold: traffic ≥ 1 request/minute")

    if requests.empty:
        st.info("Chưa có request trong cửa sổ thời gian hiện tại.")
        return
    traffic = (
        requests.assign(minute=requests["ts"].dt.floor("min"))
        .groupby("minute")
        .size()
        .rename("requests_per_minute")
        .reset_index()
    )
    metric_line_chart(
        traffic,
        x="minute",
        fields=["requests_per_minute"],
        unit="requests/minute",
        threshold=1,
    )


def render_errors(frame: pd.DataFrame) -> None:
    requests = request_events(frame)
    failures = (
        frame.loc[frame["event"] == "request_failed"].copy()
        if not frame.empty and "event" in frame.columns
        else pd.DataFrame()
    )
    tool_rows = (
        frame.loc[frame["tool_success"].notna()].copy()
        if not frame.empty and "tool_success" in frame.columns
        else pd.DataFrame()
    )
    error_rate = (len(failures) / len(requests) * 100) if len(requests) else 0.0
    retrieval_success = (
        tool_rows["tool_success"].astype(bool).mean() * 100
        if not tool_rows.empty
        else 0.0
    )

    st.subheader("3. Error rate and retrieval success")
    columns = st.columns(2)
    columns[0].metric("Error rate", f"{error_rate:.2f}%")
    columns[1].metric("Retrieval success", f"{retrieval_success:.2f}%")
    st.caption("Thresholds: error rate ≤ 2%; retrieval success ≥ 90%")

    if requests.empty:
        st.info("Chưa có request trong cửa sổ thời gian hiện tại.")
        return
    request_counts = (
        requests.assign(minute=requests["ts"].dt.floor("min"))
        .groupby("minute")
        .size()
        .rename("requests")
    )
    failure_counts = (
        failures.assign(minute=failures["ts"].dt.floor("min"))
        .groupby("minute")
        .size()
        .rename("failures")
        if not failures.empty
        else pd.Series(dtype="int64", name="failures")
    )
    errors = pd.concat([request_counts, failure_counts], axis=1).fillna(0)
    errors.index.name = "minute"
    errors["error_rate_pct"] = errors["failures"] / errors["requests"] * 100
    metric_line_chart(
        errors.reset_index(),
        x="minute",
        fields=["error_rate_pct"],
        unit="percent",
        threshold=2,
    )

    if not failures.empty and "error_type" in failures.columns:
        breakdown = failures["error_type"].fillna("Unknown").value_counts()
        st.caption("Error breakdown")
        st.bar_chart(breakdown, horizontal=True)


def render_cost(frame: pd.DataFrame) -> None:
    responses = response_events(frame)
    costs = numeric(responses, "cost_usd")
    total_cost = float(costs.sum()) if not costs.empty else 0.0

    st.subheader("4. Cost over time")
    st.metric("Total cost", f"${total_cost:.6f}", help="Unit: USD")
    st.caption("Threshold: total cost ≤ 2.5 USD")
    if responses.empty or "cost_usd" not in responses.columns:
        st.info("Chưa có dữ liệu cost trong cửa sổ thời gian hiện tại.")
        return
    cost_data = responses[["ts", "cost_usd"]].copy()
    cost_data["cost_usd"] = pd.to_numeric(cost_data["cost_usd"], errors="coerce")
    cost_data = cost_data.dropna(subset=["cost_usd"])
    cost_data["cumulative_cost_usd"] = cost_data["cost_usd"].cumsum()
    metric_line_chart(
        cost_data,
        x="ts",
        fields=["cumulative_cost_usd"],
        unit="USD",
        threshold=2.5,
    )


def render_tokens(frame: pd.DataFrame) -> None:
    responses = response_events(frame)
    tokens_in = numeric(responses, "tokens_in")
    tokens_out = numeric(responses, "tokens_out")

    st.subheader("5. Input and output tokens")
    columns = st.columns(2)
    columns[0].metric("Input tokens", f"{int(tokens_in.sum()):,}")
    columns[1].metric("Output tokens", f"{int(tokens_out.sum()):,}")
    st.caption("Threshold: total tokens per field ≤ 50,000")
    if responses.empty:
        st.info("Chưa có dữ liệu token trong cửa sổ thời gian hiện tại.")
        return
    token_data = responses[["ts"]].copy()
    token_data["tokens_in"] = pd.to_numeric(
        responses.get("tokens_in"), errors="coerce"
    ).fillna(0)
    token_data["tokens_out"] = pd.to_numeric(
        responses.get("tokens_out"), errors="coerce"
    ).fillna(0)
    token_data["input_tokens_cumulative"] = token_data["tokens_in"].cumsum()
    token_data["output_tokens_cumulative"] = token_data["tokens_out"].cumsum()
    metric_line_chart(
        token_data,
        x="ts",
        fields=["input_tokens_cumulative", "output_tokens_cumulative"],
        unit="tokens",
        threshold=50000,
    )


def render_quality(frame: pd.DataFrame) -> None:
    responses = response_events(frame)
    quality = numeric(responses, "quality_score")
    quality_avg = float(quality.mean()) if not quality.empty else 0.0

    st.subheader("6. Quality proxy")
    st.metric("Average quality score", f"{quality_avg:.3f}", help="Unit: 0–1")
    st.caption("Threshold: average quality score ≥ 0.75")
    metric_line_chart(
        responses,
        x="ts",
        fields=["quality_score"],
        unit="score (0–1)",
        threshold=0.75,
    )


@st.fragment(run_every=f"{REFRESH_SECONDS}s")
def render_dashboard() -> None:
    frame = load_logs()
    latest = frame["ts"].max() if not frame.empty else None
    latest_text = latest.strftime("%Y-%m-%d %H:%M:%S UTC") if latest is not None else "N/A"
    st.caption(
        f"Source: data/logs.jsonl · Time range: last {TIME_RANGE_MINUTES} minutes · "
        f"Auto refresh: {REFRESH_SECONDS}s · Latest event: {latest_text}"
    )

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            render_latency(frame)
    with right:
        with st.container(border=True):
            render_traffic(frame)

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            render_errors(frame)
    with right:
        with st.container(border=True):
            render_cost(frame)

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            render_tokens(frame)
    with right:
        with st.container(border=True):
            render_quality(frame)


def main() -> None:
    st.set_page_config(
        page_title="K4-L3B Monitoring & LLMOps",
        page_icon="📊",
        layout="wide",
    )
    st.title("K4-L3B Day 13 — Monitoring & LLMOps")
    render_dashboard()


if __name__ == "__main__":
    main()
