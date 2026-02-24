"""
visualize.py - Reusable visualization module for Fraudasaurus.ai

All plotting functions accept a DataFrame (or graph) and return a matplotlib
Figure (or plotly Figure where noted).  An optional ``save_path`` parameter
persists the figure to disk when provided.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from sklearn.decomposition import PCA

# ---------------------------------------------------------------------------
# Module-level style
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid")

PALETTE = sns.color_palette("muted")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _maybe_save(fig: Figure, save_path: Optional[str]) -> None:
    """Save *fig* to *save_path* if the caller supplied one."""
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight", dpi=150)


# ---------------------------------------------------------------------------
# 1. Amount histogram with structuring threshold
# ---------------------------------------------------------------------------

def plot_amount_histogram(
    df: pd.DataFrame,
    amount_col: str = "amount",
    threshold: float = 10_000,
    save_path: Optional[str] = None,
) -> Figure:
    """Histogram of transaction amounts with a vertical red dashed line at
    the structuring-evidence threshold (default $10 000).

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a numeric column named *amount_col*.
    amount_col : str
        Column holding transaction dollar amounts.
    threshold : float
        Dollar value at which to draw the structuring threshold line.
    save_path : str or None
        If provided, the figure is saved to this path.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.hist(
        df[amount_col].dropna(),
        bins=60,
        color=PALETTE[0],
        edgecolor="white",
        alpha=0.85,
    )
    ax.axvline(
        threshold,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label=f"Structuring threshold (${threshold:,.0f})",
    )

    ax.set_xlabel("Transaction Amount ($)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Transaction Amounts")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.legend()

    fig.tight_layout()
    _maybe_save(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 2. Transaction volume by time period
# ---------------------------------------------------------------------------

def plot_volume_by_time(
    df: pd.DataFrame,
    date_col: str = "transaction_date",
    freq: str = "D",
    save_path: Optional[str] = None,
) -> Figure:
    """Bar chart of transaction count aggregated by *freq* (day, hour, etc.).

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a datetime-coercible column named *date_col*.
    date_col : str
        Column holding transaction timestamps.
    freq : str
        Pandas offset alias for the resampling frequency (e.g. ``"D"``,
        ``"h"``, ``"W"``).
    save_path : str or None
        If provided, the figure is saved to this path.

    Returns
    -------
    matplotlib.figure.Figure
    """
    series = pd.to_datetime(df[date_col])
    counts = series.dt.floor(freq).value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(counts.index, counts.values, color=PALETTE[1], width=0.8)

    ax.set_xlabel("Date" if freq.upper() in {"D", "W", "M"} else "Time")
    ax.set_ylabel("Transaction Count")
    ax.set_title(f"Transaction Volume by {'Day' if freq == 'D' else freq}")

    fig.autofmt_xdate()
    fig.tight_layout()
    _maybe_save(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 3. Risk-score heatmap
# ---------------------------------------------------------------------------

def plot_risk_heatmap(
    scores_df: pd.DataFrame,
    save_path: Optional[str] = None,
) -> Figure:
    """Heatmap with accounts on the y-axis, detector names on the x-axis,
    and cells colored by risk score.

    Parameters
    ----------
    scores_df : pd.DataFrame
        Index = account identifiers, columns = detector names, values =
        numeric risk scores (0-1 recommended).
    save_path : str or None
        If provided, the figure is saved to this path.

    Returns
    -------
    matplotlib.figure.Figure
    """
    n_rows = max(4, len(scores_df) * 0.4)
    fig, ax = plt.subplots(figsize=(max(8, len(scores_df.columns) * 1.2), n_rows))

    sns.heatmap(
        scores_df,
        annot=True,
        fmt=".2f",
        cmap="YlOrRd",
        linewidths=0.5,
        ax=ax,
        vmin=0,
        vmax=1,
        cbar_kws={"label": "Risk Score"},
    )

    ax.set_ylabel("Account")
    ax.set_xlabel("Detector")
    ax.set_title("Risk Scores by Account and Detector")

    fig.tight_layout()
    _maybe_save(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 4. Network graph with optional cycle highlighting
# ---------------------------------------------------------------------------

def plot_network_graph(
    G: nx.Graph,
    highlight_cycles: Optional[List[List]] = None,
    save_path: Optional[str] = None,
) -> Figure:
    """Draw a NetworkX graph using a spring layout.  Optionally highlight
    edges that belong to cycles in red.

    Parameters
    ----------
    G : networkx.Graph or networkx.DiGraph
        The graph to visualize.
    highlight_cycles : list of lists, optional
        Each inner list is an ordered sequence of nodes forming a cycle.
        Edges along these cycles are drawn in red.
    save_path : str or None
        If provided, the figure is saved to this path.

    Returns
    -------
    matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    pos = nx.spring_layout(G, seed=42, k=1.5 / np.sqrt(max(len(G), 1)))

    # Determine cycle edges for highlighting
    cycle_edges: set = set()
    if highlight_cycles:
        for cycle in highlight_cycles:
            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                cycle_edges.add((u, v))
                cycle_edges.add((v, u))  # undirected match

    normal_edges = [e for e in G.edges() if (e[0], e[1]) not in cycle_edges]
    red_edges = [e for e in G.edges() if (e[0], e[1]) in cycle_edges]

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=PALETTE[0], node_size=350, alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)

    # Draw normal edges
    if normal_edges:
        nx.draw_networkx_edges(G, pos, edgelist=normal_edges, ax=ax, alpha=0.4, width=1.0)

    # Draw cycle edges in red
    if red_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=red_edges, ax=ax,
            edge_color="red", width=2.5, alpha=0.8,
            style="solid", label="Cycle edges",
        )
        ax.legend(scatterpoints=1, fontsize=9)

    ax.set_title("Transaction Network Graph")
    ax.axis("off")

    fig.tight_layout()
    _maybe_save(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 5. Account timeline
# ---------------------------------------------------------------------------

def plot_account_timeline(
    df: pd.DataFrame,
    account_id: str,
    date_col: str = "transaction_date",
    amount_col: str = "amount",
    save_path: Optional[str] = None,
) -> Figure:
    """Timeline scatter of transactions for a single account, colored by
    transaction type (deposit vs. withdrawal).

    Parameters
    ----------
    df : pd.DataFrame
        Transaction-level data.  Must contain columns for dates, amounts,
        an account identifier, and a ``type`` column with values like
        ``"deposit"`` or ``"withdrawal"``.
    account_id : str
        The account to filter on.  Matched against the ``account_id``
        column in *df*.
    date_col : str
        Column holding transaction timestamps.
    amount_col : str
        Column holding dollar amounts.
    save_path : str or None
        If provided, the figure is saved to this path.

    Returns
    -------
    matplotlib.figure.Figure
    """
    acct_df = df[df["account_id"] == account_id].copy()
    acct_df[date_col] = pd.to_datetime(acct_df[date_col])

    fig, ax = plt.subplots(figsize=(12, 5))

    type_col = "type" if "type" in acct_df.columns else None
    color_map = {"deposit": PALETTE[2], "withdrawal": PALETTE[3]}

    if type_col and not acct_df[type_col].isna().all():
        for txn_type, group in acct_df.groupby(type_col):
            color = color_map.get(str(txn_type).lower(), PALETTE[4])
            ax.scatter(
                group[date_col],
                group[amount_col],
                label=str(txn_type).title(),
                color=color,
                s=50,
                alpha=0.75,
                edgecolors="white",
                linewidths=0.5,
            )
        ax.legend(title="Transaction Type")
    else:
        ax.scatter(
            acct_df[date_col],
            acct_df[amount_col],
            color=PALETTE[0],
            s=50,
            alpha=0.75,
            edgecolors="white",
            linewidths=0.5,
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("Amount ($)")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_title(f"Transaction Timeline - Account {account_id}")

    fig.autofmt_xdate()
    fig.tight_layout()
    _maybe_save(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 6. Anomaly scatter (PCA 2-D projection)
# ---------------------------------------------------------------------------

def plot_anomaly_scatter(
    features_df: pd.DataFrame,
    labels: Optional[Sequence[int]] = None,
    save_path: Optional[str] = None,
) -> Figure:
    """PCA 2-D projection of a feature matrix, optionally colored by
    anomaly labels.

    Parameters
    ----------
    features_df : pd.DataFrame
        Numeric feature matrix (rows = observations, columns = features).
    labels : array-like of int, optional
        Anomaly labels per observation.  Convention: ``-1`` = anomaly,
        ``1`` = normal (scikit-learn Isolation Forest style).  If *None*,
        all points are drawn in a single color.
    save_path : str or None
        If provided, the figure is saved to this path.

    Returns
    -------
    matplotlib.figure.Figure
    """
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(features_df.select_dtypes(include=[np.number]).fillna(0))

    fig, ax = plt.subplots(figsize=(10, 7))

    if labels is not None:
        labels_arr = np.asarray(labels)
        is_anomaly = labels_arr == -1

        ax.scatter(
            coords[~is_anomaly, 0],
            coords[~is_anomaly, 1],
            c=[PALETTE[0]],
            label="Normal",
            s=30,
            alpha=0.6,
            edgecolors="white",
            linewidths=0.3,
        )
        ax.scatter(
            coords[is_anomaly, 0],
            coords[is_anomaly, 1],
            c=["red"],
            label="Anomaly",
            s=60,
            marker="x",
            alpha=0.9,
        )
        ax.legend(title="Label")
    else:
        ax.scatter(
            coords[:, 0],
            coords[:, 1],
            c=[PALETTE[0]],
            s=30,
            alpha=0.6,
            edgecolors="white",
            linewidths=0.3,
        )

    explained = pca.explained_variance_ratio_
    ax.set_xlabel(f"PC 1 ({explained[0]:.1%} variance)")
    ax.set_ylabel(f"PC 2 ({explained[1]:.1%} variance)")
    ax.set_title("Anomaly Detection - PCA Projection")

    fig.tight_layout()
    _maybe_save(fig, save_path)
    return fig
