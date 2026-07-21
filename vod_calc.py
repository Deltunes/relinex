import h5py
import pandas as pd
import numpy as np
import glob
import os
import re
import matplotlib.pyplot as plt

MAX_TIME_DIFF_MS = 100

# Read elevation data.
# New sat_elevation.csv format:
# gps_week,tow_ms,prn,azimuth_deg,elevation_deg
elev = pd.read_csv(
    "BLOCKED/sat_elevation.csv",
    names=[
        "gps_week",
        "tow_ms",
        "prn",
        "azimuth_deg",
        "elevation_deg"
    ],
    dtype={"prn": str}
)

# Make sure numerical columns are actually numeric.
elev["gps_week"] = pd.to_numeric(
    elev["gps_week"],
    errors="coerce"
)

elev["tow_ms"] = pd.to_numeric(
    elev["tow_ms"],
    errors="coerce"
)

elev["azimuth_deg"] = pd.to_numeric(
    elev["azimuth_deg"],
    errors="coerce"
)

elev["elevation_deg"] = pd.to_numeric(
    elev["elevation_deg"],
    errors="coerce"
)

# Remove malformed rows.
elev = elev.dropna(
    subset=[
        "gps_week",
        "tow_ms",
        "prn",
        "elevation_deg"
    ]
)

# Remove accidental spaces around satellite identifiers.
elev["prn"] = elev["prn"].str.strip()

# Read the exact channel-to-satellite order used by the config generator.
top4 = pd.read_csv(
    "top4_sats.txt",
    sep=r"\s+",
    names=["prn", "carrier_phase", "doppler"],
    dtype={"prn": str}
)

# Line 0 in top4_sats.txt becomes Channel0, line 1 becomes Channel1, etc.
channel_to_prn = {
    channel_number: prn
    for channel_number, prn in enumerate(top4["prn"])
}

print("Channel mapping:")

for channel_number, prn in channel_to_prn.items():
    print(f"  Channel {channel_number} -> {prn}")

results = []

for open_file in sorted(glob.glob("OPEN/tracking_ch_*.mat")):
    name = os.path.basename(open_file)

    # Extract the channel number from tracking_ch_0.mat, tracking_ch_1.mat, etc.
    channel_match = re.search(r"tracking_ch_(\d+)\.mat$", name)

    if channel_match is None:
        print(f"Skipping {name}: could not read channel number")
        continue

    channel_number = int(channel_match.group(1))

    # Get the complete constellation + PRN from top4_sats.txt.
    if channel_number not in channel_to_prn:
        print(
            f"Skipping {name}: channel {channel_number} "
            f"is not listed in top4_sats.txt"
        )
        continue

    prn = channel_to_prn[channel_number]

    blocked_file = os.path.join("BLOCKED", name)

    if not os.path.exists(blocked_file):
        print(f"Skipping {name}: missing matching blocked file")
        continue

    with h5py.File(open_file, "r") as open_mat, \
         h5py.File(blocked_file, "r") as blocked_mat:

        # The .mat files normally store only the numeric PRN.
        open_prn_number = int(open_mat["PRN"][0][0])
        blocked_prn_number = int(blocked_mat["PRN"][0][0])

        expected_prn_number = int(prn[1:])

        # Safety check: confirm both files contain the expected numeric PRN.
        if open_prn_number != expected_prn_number:
            print(
                f"Skipping {name}: top4_sats says {prn}, "
                f"but OPEN file says PRN {open_prn_number}"
            )
            continue

        if blocked_prn_number != expected_prn_number:
            print(
                f"Skipping {name}: top4_sats says {prn}, "
                f"but BLOCKED file says PRN {blocked_prn_number}"
            )
            continue

        open_cn0 = open_mat["CN0_SNV_dB_Hz"][:].flatten()
        open_tow = open_mat["TOW_ms"][:].flatten()

        blocked_cn0 = blocked_mat["CN0_SNV_dB_Hz"][:].flatten()
        blocked_tow = blocked_mat["TOW_ms"][:].flatten()

    if len(open_cn0) != len(open_tow):
        print(f"Skipping {name}: OPEN C/N0 and TOW lengths differ")
        continue

    if len(blocked_cn0) != len(blocked_tow):
        print(f"Skipping {name}: BLOCKED C/N0 and TOW lengths differ")
        continue

    # This now matches the full identifier: G13 or E13, not just 13.
    this_elev = (
        elev[elev["prn"] == prn]
        .sort_values(["gps_week", "tow_ms"])
        .reset_index(drop=True)
    )

    if this_elev.empty:
        print(f"Skipping {prn}: no elevation data")
        continue

    elev_tow = this_elev["tow_ms"].to_numpy()

    vod_values = []

    for i in range(len(blocked_tow)):
        btow = blocked_tow[i]
        blocked_value = blocked_cn0[i]

        if (
            not np.isfinite(btow)
            or not np.isfinite(blocked_value)
            or btow <= 0
            or blocked_value <= 0
        ):
            continue

        # Find the most recent OPEN measurement at or before this BLOCKED time.
        open_matches = np.where(
            (open_tow <= btow)
            & ((btow - open_tow) <= MAX_TIME_DIFF_MS)
        )[0]

        if len(open_matches) == 0:
            continue

        open_idx = open_matches[-1]

        # Find the most recent elevation measurement at or before this time.
        elev_matches = np.where(
            (elev_tow <= btow)
            & ((btow - elev_tow) <= MAX_TIME_DIFF_MS)
        )[0]

        if len(elev_matches) == 0:
            continue

        elev_idx = elev_matches[-1]

        open_value = open_cn0[open_idx]
        elevation_deg = this_elev.iloc[elev_idx]["elevation_deg"]

        if (
            not np.isfinite(open_value)
            or not np.isfinite(elevation_deg)
            or open_value <= 0
            or elevation_deg <= 0
        ):
            continue

        E = np.radians(elevation_deg)

        # Convert the dB-Hz difference into a linear ratio.
        ratio = 10 ** ((blocked_value - open_value) / 10)

        # np.log is the natural logarithm.
        vod = -np.sin(E) * np.log(ratio)

        if np.isfinite(vod):
            vod_values.append(vod)

    if len(vod_values) > 0:
        results.append(
            [
                channel_number,
                prn,
                prn[0],
                np.mean(vod_values),
                np.median(vod_values),
                len(vod_values)
            ]
        )

        print(
            f"{name}: {prn}, "
            f"{len(vod_values)} valid VOD values"
        )
    else:
        print(f"No valid VOD values for {prn}")

df = pd.DataFrame(
    results,
    columns=[
        "Channel",
        "PRN",
        "Constellation",
        "Average_VOD",
        "Median_VOD",
        "Num_Values"
    ]
)

print(df)

df.to_csv("vod_results.csv", index=False)
print("Saved vod_results.csv")

# Keep only the first four channels.
top4_df = (
    df[df["Channel"].isin([0, 1, 2, 3])]
    .sort_values("Channel")
    .reset_index(drop=True)
)

if top4_df.empty:
    print("No VOD results available to graph.")
else:
    plt.figure(figsize=(9, 6))

    labels = [
        f"Channel {row.Channel}\n{row.PRN}"
        for row in top4_df.itertuples()
    ]

    bars = plt.bar(
        labels,
        top4_df["Average_VOD"]
    )

    # Print the numerical VOD value above or below each bar.
    for bar, vod_value in zip(bars, top4_df["Average_VOD"]):
        x_position = bar.get_x() + bar.get_width() / 2

        if vod_value >= 0:
            y_position = vod_value
            vertical_alignment = "bottom"
        else:
            y_position = vod_value
            vertical_alignment = "top"

        plt.text(
            x_position,
            y_position,
            f"{vod_value:.6f}",
            ha="center",
            va=vertical_alignment,
            fontsize=10
        )

    plt.axhline(0, linewidth=1)

    plt.title("Average Vegetation Optical Depth by Channel")
    plt.xlabel("GNSS-SDR Channel and Satellite")
    plt.ylabel("Average VOD")

    plt.tight_layout()
    plt.savefig("vod_top4_channels.png", dpi=300)
    plt.show()

    print("Saved vod_top4_channels.png")
