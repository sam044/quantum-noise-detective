"""Interactive lab. Every displayed measurement and prediction comes from the local API."""

import json
import os
import secrets
from datetime import datetime

import httpx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

API = os.environ.get("QND_API_URL", "http://127.0.0.1:8765")
PUBLIC = os.environ.get("QND_PUBLIC", "0") == "1"
NAMES = {"baseline": "Conventional fit", "torch": "PyTorch model", "tensorflow": "TensorFlow model"}
COLORS = {"baseline": "#ffbf69", "torch": "#60d5fa", "tensorflow": "#bf9cff", "truth": "#7be0b1"}

st.set_page_config(page_title="Quantum Noise Detective", page_icon="⚛", layout="wide")
st.markdown(
    """<style>
.block-container {max-width:1440px;padding-top:4rem;padding-bottom:2rem;}
h1 {letter-spacing:-.045em;font-weight:650!important;}
h2,h3 {letter-spacing:-.02em;}
[data-testid="stMetric"] {background:#131e30;border:1px solid #26364e;border-radius:12px;padding:16px;}
[data-testid="stMetricLabel"] {color:#b8c9df;}
[data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;}
[data-testid="stSidebar"] {border-right:1px solid #26364e;}
.q-eyebrow {font-size:12px;letter-spacing:.16em;color:#60d5fa;margin-bottom:6px;}
.q-intro {color:#b8c9df;max-width:750px;margin-bottom:22px;}
.q-rule {height:1px;background:#26364e;margin:18px 0;}
</style>""",
    unsafe_allow_html=True,
)


def request(method, route, **kwargs):
    if "visitor_token" not in st.session_state:
        st.session_state.visitor_token = secrets.token_urlsafe(32)
    try:
        response = httpx.request(
            method, API + route, timeout=30,
            headers={"X-QND-Visitor": st.session_state.visitor_token}, **kwargs
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json().get("detail", str(error))
        except ValueError:
            detail = str(error)
        st.error(f"The request could not be completed: {detail}")
    except httpx.RequestError:
        st.error(
            "The lab is temporarily unavailable. Please refresh in a moment."
            if PUBLIC else
            "The local lab service is unavailable. Start the app using launch.py, then refresh."
        )
    st.stop()


def time_label(value):
    return "∞" if value is None else f"{value:.1f} µs"


def refresh_experiment():
    st.session_state.experiment = request(
        "GET", f"/experiments/{st.session_state.experiment['id']}"
    )


def chart(ex, protocol):
    counts = np.array(ex["counts"])[protocol]
    times = ex["times_us"]
    fig = go.Figure()
    frequencies = counts / ex["shots"]
    # The error bars describe measurement sampling, not uncertainty in inferred rates.
    # Wilson score half-widths stay nonzero at boundary frequencies.
    z, n = 1.96, ex["shots"]
    center = (frequencies + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(frequencies * (1 - frequencies) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    fig.add_trace(
        go.Scatter(
            x=times,
            y=frequencies,
            name="Measurements",
            mode="markers",
            marker={"color": "#d6e2f2", "size": 5},
            error_y={
                "type": "data",
                "array": center + half - frequencies,
                "arrayminus": frequencies - center + half,
                "symmetric": False,
                "thickness": 0.7,
                "width": 0,
                "color": "#53657f",
            },
            hovertemplate="Delay %{x:.1f} µs<br>Observed probability %{y:.3f}<extra>Measurements</extra>",
        )
    )
    for method, result in ex["diagnoses"].items():
        fig.add_trace(
            go.Scatter(
                x=times,
                y=result["curves"][protocol],
                name=NAMES[method],
                mode="lines",
                line={
                    "color": COLORS[method],
                    "width": 2.5,
                    "dash": "dash"
                    if method == "baseline"
                    else "dot"
                    if method == "tensorflow"
                    else "solid",
                },
            )
        )
    if ex["revealed"]:
        truth = ex["truth"]
        t = np.array(times)
        y = (
            np.exp(-truth["gamma1"] * t)
            if protocol == 0
            else (1 + np.exp(-(truth["gamma1"] / 2 + truth["gamma_phi"]) * t)) / 2
        )
        fig.add_trace(
            go.Scatter(
                x=times,
                y=y,
                name="Simulator truth",
                mode="lines",
                line={"color": COLORS["truth"], "width": 2, "dash": "longdash"},
            )
        )
    fig.update_layout(
        height=320,
        margin={"l": 5, "r": 15, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#b8c9df"},
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.3, "font": {"size": 11}},
        xaxis={"title": "Delay (µs)", "gridcolor": "#223047", "range": [0, 300]},
        yaxis={
            "title": "P(excited)" if protocol == 0 else "P(+)",
            "gridcolor": "#223047",
            "range": [-0.03, 1.05],
        },
    )
    return fig


def result_table(ex):
    rows = []
    for method, r in ex["diagnoses"].items():
        row = {
            "Estimator": NAMES[method],
            "T1": time_label(r["t1_us"]),
            "Tφ": time_label(r["tphi_us"]),
            "T2": time_label(r["t2_us"]),
            "γ1 (µs⁻¹)": f"{r['gamma1']:.5f}",
            "γφ (µs⁻¹)": f"{r['gamma_phi']:.5f}",
            "Compute (ms)": round(r["latency_ms"], 3),
        }
        if ex["revealed"]:
            for key, label in [("gamma1", "γ1 error"), ("gamma_phi", "γφ error")]:
                true = ex["truth"][key]
                row[label] = (
                    f"{abs(r[key] / true - 1) * 100:.1f}%" if true > 0 else "Zero-rate truth"
                )
        rows.append(row)
    return pd.DataFrame(rows)


if "next_page" in st.session_state:
    st.session_state.page = st.session_state.pop("next_page")
health = request("GET", "/health")
with st.sidebar:
    st.markdown("### ⚛  Quantum lab")
    st.caption("NOISE DETECTIVE / v0.1")
    page = st.radio(
        "Workspace",
        ["Experiment lab", "Model comparison", "Experiment history", "Field guide"],
        key="page",
    )
    st.divider()
    st.caption("SYNTHETIC EXPERIMENTS • NO QUANTUM HARDWARE")
    st.write("One qubit. Two noise sources.")
    st.caption(
        "A quantum system loses energy and phase coherence. Can we infer how quickly from measurements alone?"
    )
    ready = sum(health["models"].values())
    st.caption(f"{ready}/2 trained models available · CPU inference")
    if PUBLIC:
        st.caption(
            "History belongs to this session and expires after 7 days. "
            "A refresh or reconnect may start a new session. Download JSON to keep your results."
        )

st.markdown(
    '<div class="q-eyebrow">QUANTUM SYSTEMS / MACHINE LEARNING</div>', unsafe_allow_html=True
)
st.title("Quantum Noise Detective")

if page == "Experiment lab":
    st.markdown(
        '<div class="q-intro">Measure a simulated qubit. Diagnose its noise. Reveal the answer.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Configure an experiment", expanded="experiment" not in st.session_state):
        with st.form("experiment_config"):
            a, b, c = st.columns([1.1, 1.1, 1])
            mode = a.selectbox("Experiment mode", ["Mystery noise", "Choose noise settings"])
            t1 = b.slider("Energy relaxation time T1 (µs)", 10, 100, 50)
            phi = b.slider("Pure dephasing time Tφ (µs)", 10, 200, 80)
            a.caption(
                "Mystery mode ignores the sliders and hides the simulator's parameters until reveal."
            )
            shots = c.selectbox("Shots per delay", [256, 64, 1024])
            c.caption("256 enables all models. Other shot counts use conventional fitting.")
            label = a.text_input(
                "Experiment name", value="Single-qubit investigation", max_chars=80
            )
            generate = st.form_submit_button("Generate experiment", type="primary")
        if generate:
            payload = {
                "mode": "mystery" if mode == "Mystery noise" else "custom",
                "shots": shots,
                "label": label.strip() or "Single-qubit investigation",
            }
            if payload["mode"] == "custom":
                payload.update(gamma1=1 / t1, gamma_phi=1 / phi)
            st.session_state.experiment = request("POST", "/experiments", json=payload)
            st.session_state.selected_method = "baseline"
            st.rerun()
    if "experiment" not in st.session_state:
        st.session_state.experiment = request(
            "POST", "/experiments", json={"label": "Welcome experiment"}
        )
    ex = st.session_state.experiment
    st.caption(
        f"{ex['label']} · {ex['id'][:8]} · 64 delays × {ex['shots']} shots × 2 protocols · Automatically saved"
    )
    controls = st.columns([2, 1, 1, 1])
    methods = ["baseline"] + [
        m for m, ready in health["models"].items() if ready and ex["shots"] == 256
    ]
    if st.session_state.get("selected_method") not in methods:
        st.session_state.selected_method = "torch" if "torch" in methods else "baseline"
    method = controls[0].selectbox(
        "Estimator", methods, format_func=lambda m: NAMES[m], key="selected_method"
    )
    with controls[1]:
        st.write("")
        run = st.button("Diagnose", type="primary", width="stretch")
    with controls[2]:
        st.write("")
        compare = st.button("Compare methods", width="stretch")
    with controls[3]:
        st.write("")
        reveal = st.button("Reveal truth", disabled=ex["revealed"], width="stretch")
    if run or compare:
        with st.spinner("Reading the measurement evidence…"):
            for m in methods if compare else [method]:
                request("POST", f"/experiments/{ex['id']}/diagnose/{m}")
            refresh_experiment()
        st.rerun()
    if reveal:
        st.session_state.experiment = request("POST", f"/experiments/{ex['id']}/reveal")
        st.rerun()
    result = ex["diagnoses"].get(method)
    if result:
        c1, c2, c3 = st.columns(3)
        c1.metric("Energy relaxation · T1", time_label(result["t1_us"]))
        c2.metric("Pure dephasing · Tφ", time_label(result["tphi_us"]))
        c3.metric("Overall coherence · T2", time_label(result["t2_us"]))
        if not result["converged"]:
            st.warning(
                "The conventional optimizer did not converge. Treat this estimate as provisional."
            )
    else:
        st.info("The measurements are ready. Choose an estimator and press Diagnose.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("01 / Energy relaxation")
        st.caption("How long does the qubit remain excited?")
        st.plotly_chart(chart(ex, 0), width="stretch", key="energy_chart")
    with c2:
        st.subheader("02 / Coherence decay")
        st.caption("How long does its phase information survive?")
        st.plotly_chart(chart(ex, 1), width="stretch", key="coherence_chart")
    st.caption(
        "Dots are repeated measurement frequencies. Whiskers are 95% Wilson sampling intervals; they are not model-confidence intervals."
    )
    if ex["revealed"]:
        truth = ex["truth"]
        st.success(
            f"Simulator truth · T1 = {time_label(truth['t1_us'])} · Tφ = {time_label(truth['tphi_us'])} · T2 = {time_label(truth['t2_us'])}"
        )
    if ex["diagnoses"]:
        st.subheader("Diagnosis report")
        st.dataframe(result_table(ex), hide_index=True, width="stretch")
        if result:
            if result["intervals"]:
                st.markdown("**90% marginal prediction intervals**")
                intervals = result["intervals"]
                a, b = st.columns(2)
                a.write(f"Relaxation rate γ1: **{intervals[0][0]:.5f}–{intervals[0][1]:.5f} µs⁻¹**")
                b.write(
                    f"Pure-dephasing rate γφ: **{intervals[1][0]:.5f}–{intervals[1][1]:.5f} µs⁻¹**"
                )
            st.caption(result["interval_note"])
            if "scope_note" in result:
                st.caption(result["scope_note"])
    st.download_button(
        "Download experiment JSON",
        json.dumps(ex, indent=2),
        file_name=f"experiment-{ex['id'][:8]}.json",
        mime="application/json",
    )

elif page == "Model comparison":
    st.markdown(
        '<div class="q-intro">Held-out experiments. Measured performance. No assumed advantage.</div>',
        unsafe_allow_html=True,
    )
    response = httpx.get(API + "/benchmark", timeout=15)
    if response.status_code == 404:
        st.info("The benchmark is still being prepared. You can use the experiment lab now.")
        st.stop()
    if response.status_code != 200:
        st.error("The benchmark could not be loaded.")
        st.stop()
    report = response.json()
    a, b, c = st.columns(3)
    a.metric("Unseen test experiments", f"{report['n_test']:,}")
    b.metric(
        "Independent calibration experiments", f"{report['dataset']['sizes']['calibration']:,}"
    )
    c.metric("Measurements per delay", "256 shots")
    rows = []
    for name, r in report["methods"].items():
        rows.append(
            {
                "Estimator": NAMES[name],
                "γ1 median error (%)": r["median_relative_error_pct"][0],
                "γφ median error (%)": r["median_relative_error_pct"][1],
                "Median compute (ms)": r["median_latency_ms"],
                "γ1 interval coverage (%)": r["coverage"][0] * 100 if r["coverage"] else None,
                "γφ interval coverage (%)": r["coverage"][1] * 100 if r["coverage"] else None,
                "Unconverged fits": r.get("failures", 0),
            }
        )
    st.subheader("Accuracy and speed")
    st.dataframe(pd.DataFrame(rows).round(3), hide_index=True, width="stretch")
    fig = go.Figure()
    for i, label in enumerate(["Energy relaxation γ1", "Pure dephasing γφ"]):
        fig.add_trace(
            go.Bar(
                name=label,
                x=[NAMES[m] for m in report["methods"]],
                y=[r["median_relative_error_pct"][i] for r in report["methods"].values()],
                marker_color=["#60d5fa", "#bf9cff"][i],
            )
        )
    fig.update_layout(
        height=300,
        barmode="group",
        yaxis_title="Median relative error (%)",
        margin={"t": 10, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": 1.15},
    )
    st.plotly_chart(fig, width="stretch")
    for note in report["notes"]:
        st.caption(note)
    st.subheader("Where the models struggle")
    stress_rows = []
    for condition, results in report["stress_tests"].items():
        for name, r in results.items():
            stress_rows.append(
                {
                    "Stress condition": condition.replace("_", " "),
                    "Model": NAMES[name],
                    "γ1 median error (%)": round(r["median_relative_error_pct"][0], 2),
                    "γφ median error (%)": round(r["median_relative_error_pct"][1], 2),
                    "γφ coverage (%)": round(r["coverage"][1] * 100, 1),
                }
            )
    st.dataframe(stress_rows, hide_index=True, width="stretch")
    st.caption(
        "Stress tests deliberately depart from training assumptions. The production API rejects unsupported neural shot counts."
    )
    with st.expander("Training and reproducibility details"):
        for name in ["torch", "tensorflow"]:
            meta = report["methods"][name]["metadata"]
            st.write(
                f"**{NAMES[name]}** · {meta['epochs']} epochs · {meta['training_seconds']:.1f} s · {meta['model_version']}"
            )
        st.json(
            {
                "dataset_sha256": report["dataset"]["sha256"],
                "split_sizes": report["dataset"]["sizes"],
                "sampling": report["dataset"]["distribution"],
            }
        )
    st.download_button(
        "Download benchmark JSON",
        json.dumps(report, indent=2),
        file_name="quantum-noise-benchmark.json",
        mime="application/json",
    )

elif page == "Experiment history":
    st.markdown(
        '<div class="q-intro">Reopen investigations from this session, including measurements and diagnoses.</div>'
        if PUBLIC else
        '<div class="q-intro">Every investigation is saved locally, including its measurements and diagnoses.</div>',
        unsafe_allow_html=True,
    )
    experiments = request("GET", "/experiments")
    if not experiments:
        st.info("No experiments yet. Start in the experiment lab.")
    for ex in experiments:
        with st.container(border=True):
            a, b = st.columns([4, 1])
            a.markdown(f"**{ex['label']}**")
            created = (
                datetime.fromisoformat(ex["created"]).astimezone().strftime("%b %d · %I:%M %p")
            )
            a.caption(
                f"{created} · {ex['id'][:8]} · {'Truth revealed' if ex['revealed'] else 'Truth hidden'}"
            )
            if b.button("Open experiment", key=ex["id"]):
                st.session_state.experiment = request("GET", f"/experiments/{ex['id']}")
                st.session_state.next_page = "Experiment lab"
                st.rerun()

else:
    st.markdown(
        '<div class="q-intro">The physics behind the detective work, without needing a quantum computer.</div>',
        unsafe_allow_html=True,
    )
    a, b = st.columns([1, 1.2])
    with a:
        st.subheader("Two ways to lose information")
        st.markdown(
            "**Relaxation (T1)** is energy loss: an excited qubit settles toward its ground state. A shorter T1 means faster loss."
        )
        st.markdown(
            "**Pure dephasing (Tφ)** is loss of phase coherence without requiring an energy transition. Both effects determine **T2**, the overall coherence time."
        )
        st.latex(r"\frac{1}{T_2}=\frac{1}{2T_1}+\frac{1}{T_\phi}")
        st.markdown(
            "We need both experiments because energy measurements alone cannot reveal pure dephasing. Each plotted point uses freshly prepared qubits; it is not a continuous observation of one qubit."
        )
        t1 = st.slider("Explore T1 (µs)", 10, 100, 50, key="guide_t1")
        phi = st.slider("Explore Tφ (µs)", 10, 200, 80, key="guide_phi")
        delay = st.slider("Time along trajectory (µs)", 0, 300, 50)
    with b:
        st.subheader("Watch coherence fade")
        u, v = np.mgrid[0 : 2 * np.pi : 24j, 0 : np.pi : 16j]
        fig = go.Figure(
            go.Surface(
                x=np.cos(u) * np.sin(v),
                y=np.sin(u) * np.sin(v),
                z=np.cos(v),
                opacity=0.09,
                showscale=False,
                colorscale=[[0, "#60d5fa"], [1, "#60d5fa"]],
                hoverinfo="skip",
            )
        )
        t = np.linspace(0, 300, 100)
        x = np.exp(-(1 / (2 * t1) + 1 / phi) * t)
        z = 1 - np.exp(-t / t1)
        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=np.zeros_like(x),
                z=z,
                mode="lines",
                name="State trajectory",
                line={"color": "#60d5fa", "width": 6},
            )
        )
        nowx, nowz = np.exp(-(1 / (2 * t1) + 1 / phi) * delay), 1 - np.exp(-delay / t1)
        fig.add_trace(
            go.Scatter3d(
                x=[0, nowx],
                y=[0, 0],
                z=[0, nowz],
                mode="lines+markers",
                name="Current state",
                line={"color": "#ffbf69", "width": 5},
                marker={"size": 4},
            )
        )
        fig.update_layout(
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            scene={
                "xaxis": {"title": "Coherence X", "range": [-1, 1]},
                "yaxis": {"title": "Coherence Y", "range": [-1, 1]},
                "zaxis": {"title": "Population Z", "range": [-1, 1]},
                "aspectmode": "cube",
                "bgcolor": "rgba(0,0,0,0)",
            },
            legend={"orientation": "h"},
        )
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Bloch sphere: an initially coherent |+⟩ state relaxes toward |0⟩ at the north pole. Interior points represent mixed states. Drag to rotate."
        )
    st.divider()
    st.subheader("What the model does—and what it cannot claim")
    st.write(
        "A neural network learns a mapping from two measurement sequences to two noise rates. It never sees the hidden answer at inference time. Training and test experiments are separate, and the conventional fit provides a physics-based reference."
    )
    st.write(
        "The simulator assumes ideal preparation and readout, zero-temperature relaxation, no detuning, and constant Markovian rates. Real hardware can violate these assumptions. A good synthetic benchmark is not proof of a hardware diagnosis or quantum speedup."
    )
    st.markdown(
        "[QuTiP dynamics documentation](https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html)"
    )

st.divider()
st.caption(
    "Quantum Noise Detective · Python + quantum dynamics + machine learning · All experiments are simulated"
)
