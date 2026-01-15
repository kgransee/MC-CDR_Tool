
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

file_path = "/Users/kevingransee/Desktop/CDR_SI_MockData.CSV"
path = Path(file_path).expanduser()
if not path.is_file():
    raise FileNotFoundError(f"File not found: {path}")

df = pd.read_csv(path, sep=';')
print(f"Loaded file: {path}")
print("Columns:", df.columns.tolist())

def sample_empirical(rng, data, n):
    return rng.choice(data, size=n, replace=True)

def mc_estimates_and_plot(data_vec, col_name, seed=123, n_samples=100_000, B=5_000, alpha=0.05):
    """
    Bootstrap-only analysis and plotting for one column.
    Uses only numeric values from the provided vector; original df is not modified.
    Saves plot as 'bootstrap_<COLNAME>.png' and returns a result dict.
    """
    # Try to interpret the column as numeric without modifying df
    try:
        data_float = data_vec.astype(float)
    except Exception as e:
        raise TypeError(f"Column '{col_name}' is not numeric: {e}")

    # Keep only finite numeric values for computation/plotting
    mask = np.isfinite(data_float)
    data = data_float[mask]
    n_data = len(data)
    if n_data < 2:
        raise ValueError(f"Not enough numeric values in '{col_name}' to compute CI (n={n_data}).")

    rng = np.random.default_rng(seed)

    # Monte Carlo sampling from empirical distribution
    samples = sample_empirical(rng, data, n_samples)

    # Quantities of interest (relative to 0)
    prob_gt0 = float((samples > 0).mean())   # net positive SI
    prob_lt0 = float((samples < 0).mean())   # net negative SI
    prob_n   = float((samples == 0).mean())  # neutral SI
    mean_est = float(samples.mean())         # E[X] via MC resamples

    # Standard error of mean (classic) on numeric values
    s_data = float(np.std(data, ddof=1))
    se_mean_classic = float(s_data / np.sqrt(n_data))

    # Bootstrap for mean (on numeric values)
    boot_means = np.empty(B)
    for b in range(B):
        s = rng.choice(data, size=n_data, replace=True)
        boot_means[b] = np.mean(s)

    se_mean_bootstrap = float(np.std(boot_means, ddof=1))
    ci_boot_lower, ci_boot_upper = np.percentile(boot_means, [100*alpha/2, 100*(1 - alpha/2)]).astype(float)
    mean_sample = float(np.mean(data))

    # --- Visualization (bootstrap-only) ---
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    # (A) Raw numeric data strip + mean + Bootstrap CI
    y_jitter = 0.02
    axs[0].scatter(
        data,
        np.zeros_like(data, dtype=float) + y_jitter,
        alpha=0.7, color="#4C78A8", label="Data"
    )

    # Sample mean
    axs[0].axvline(
        mean_sample, color="black", linestyle="-", linewidth=2,
        label=f"Mean = {mean_sample:.2f}"
    )

    # Bootstrap CI bar
    axs[0].hlines(
        y=0.10, xmin=ci_boot_lower, xmax=ci_boot_upper,
        color="#5DA5DA", linewidth=6, label="Bootstrap CI"
    )
    axs[0].scatter([ci_boot_lower, ci_boot_upper], [0.10, 0.10], color="#5DA5DA", s=50)

    axs[0].set_title(f"Data + Bootstrap CI for {col_name} (n={n_data})")
    axs[0].set_xlabel(col_name)
    axs[0].set_yticks([])
    axs[0].legend(loc="upper right")

    # (B) Bootstrap mean distribution + CI markers
    axs[1].hist(boot_means, bins=40, color="#5DA5DA", alpha=0.75)
    axs[1].axvline(ci_boot_lower, color="#5DA5DA", linestyle="--", linewidth=2, label=f"Lower {ci_boot_lower:.2f}")
    axs[1].axvline(ci_boot_upper, color="#5DA5DA", linestyle="--", linewidth=2, label=f"Upper {ci_boot_upper:.2f}")
    axs[1].axvline(mean_sample,   color="black",    linestyle="-",  linewidth=2, label=f"Mean {mean_sample:.2f}")

    axs[1].set_title("Bootstrap Means (Percentile CI)")
    axs[1].set_xlabel("Mean value")
    axs[1].set_ylabel("Frequency")
    axs[1].legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in col_name)
    out_file = f"bootstrap_{safe_name}.png"
    plt.savefig(out_file, dpi=160)
    plt.close(fig)

    return {
        "column": col_name,
        "n": int(n_data),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "mean_sample": mean_sample,
        "E[X]_mc": mean_est,
        "prob_gt0_mc": prob_gt0,
        "prob_lt0_mc": prob_lt0,
        "prob_n": prob_n,
        "SE_mean_classic": se_mean_classic,
        "SE_mean_bootstrap": se_mean_bootstrap,
        "CI95_E[X]_bootstrap": [ci_boot_lower, ci_boot_upper],
        "plot_file": out_file
    }

# --- 4) Run for every column except 'participant' (up to 10 columns if you want) ---
results = []
exclude = {"participant"}  # case-sensitive; adjust if your file uses 'Participant'
target_cols = [c for c in df.columns if c not in exclude]

for col in target_cols:
    arr = df[col].to_numpy()  # use the column exactly as read
    try:
        res = mc_estimates_and_plot(arr, col)
        results.append(res)
        print(f"\n[{col}]")
        print(res)
    except Exception as e:
        print(f"\n[SKIPPED] Column '{col}' — reason: {e}")

