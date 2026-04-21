# VISUALIZATION.md
# Cryptic Combat - Data Visualization Documentation

This document explains the gameplay statistics visualizations used in **Cryptic Combat**.
All charts are shown inside the in-game statistics panel and are backed by data recorded during combat.
The raw dataset used for these visuals is stored in `data/raw/gameplay_stats.csv`.

---

## Overview

The statistics interface contains **5 visualization components**:
1. Summary Dashboard
2. Damage per Turn Trend
3. Time Taken per Word
4. Keystrokes per Word
5. Combo Achieved

The combat logger records one row each time the player resolves a word in battle. The tracked fields are:
- `time_taken_per_word`
- `attempts_per_word`
- `combo_achieved`
- `damage_per_turn`
- `keystrokes_per_word`

Based on the current dataset, the file contains **112 combat-word records**.

---

## 1. Summary Dashboard

![Summary Dashboard](summarized_dashboard.png)

The Summary Dashboard gives a compact performance snapshot using derived metrics from recent gameplay logs. It highlights **Tempo**, **Input Efficiency**, **Clutch Rate**, **Combo Peak**, **Burst Damage**, and **Rhythm Score**. From the current dataset, average word-solving time is **24.75 seconds**, average keystrokes per word are **26.32**, and average attempts per word are **4.16**. The dashboard would therefore report a slower and still input-heavy play pattern, which fits a word-combat system where players often retype and revise guesses before landing a hit.

Two metrics stand out immediately. First, the **Combo Peak** still reaches **x15**, but the median combo has now moved up to **x2**, which suggests the expanded sample includes more sustained streaks than before even though low-combo turns remain dominant. Second, **Burst Damage** still peaks at **60**, while the median damage has risen to **21**, showing that the baseline combat output is no longer clustered as tightly at the minimum value. The derived **Clutch Rate** is now **12.50%**, meaning only a small share of words are solved within three guesses, so the summary still presents the player as inconsistent but slightly more stable than the earlier dataset.

---

## 2. Damage per Turn Trend - Line Graph

![Damage per Turn](damage_per_turn.png)

This line graph shows the damage dealt on recent successful word resolutions. The x-axis represents the most recent combat turns shown by the UI, while the y-axis represents damage dealt. In the current log, the mean damage is **24.24**, the median is **21**, and the maximum recorded hit is **60**. Because the median still sits well below the peak, the chart is expected to show a steady low-to-mid baseline with occasional sharp spikes rather than a smooth upward progression.

That pattern reflects the actual combat design in the code. Damage rises with combo count, so high points on the line correspond to streak-driven turns rather than normal attacks. Since **18 damage** still appears most often with **46 occurrences**, while **21** and **24** damage now appear much more frequently than before, the graph communicates that the game rewards momentum heavily but also spends more time above the absolute baseline. This is useful for evaluating whether combo scaling feels exciting without making every turn equally strong.

---

## 3. Time Taken per Word - Bar Chart

![Time Taken per Word](time_taken_per_word.png)

This bar chart shows how long the player takes to solve each combat word, measured in seconds. The mean solving time is **24.75 seconds**, the median is **21.09 seconds**, the minimum is **9.10 seconds**, and the maximum reaches **97.69 seconds**. The gap between the mean and median still shows a right-skewed distribution: most words are solved at a moderate speed, but a few very slow encounters pull the average upward.

This is a meaningful performance signal for a word-based roguelike. Fast bars near the lower end suggest moments where the player quickly recognized the answer and maintained battle tempo, while unusually tall bars suggest hesitation, repeated corrections, or pressure during difficult fights. Because combat pacing affects perceived tension, this graph helps show whether the player is flowing through encounters or getting stalled by word difficulty.

---

## 4. Keystrokes per Word - Line Graph

![Keystrokes per Word](keystrokes_per_word.png)

This line graph tracks how many keyboard inputs were needed to complete each word. The average is **26.32 keystrokes per word**, the median is **24**, the minimum is **12**, and the maximum is **45**. Since a correct answer only needs a small number of ideal inputs, these values indicate that players often backspace, retry, or spend extra inputs exploring possible answers before confirming them.

The graph is especially useful when interpreted together with the time chart. If both time and keystrokes rise together, it suggests uncertainty and inefficient word entry rather than simple reading delay. The game also computes an input-efficiency style metric from this data, and with the current average the effective efficiency is now about **19.00%**, which supports the conclusion that the current recorded run involved substantial correction and trial-and-error typing.

---

## 5. Combo Achieved - Bar Chart

![Combo Achieved](combo_achieved.png)

This bar chart shows the combo multiplier reached when each word was successfully resolved. The dataset has a mean combo of **3.08**, a median of **2**, and a maximum of **15**. The distribution is still concentrated at the low end: **x1** appears **46 times** out of 112 records, while higher combo values become increasingly rare. This means the player usually lands short streaks, but the larger sample now shows more frequent mid-level momentum than the earlier version of the log.

This chart is one of the clearest indicators of risk-reward tension in the combat loop. Since combo directly amplifies damage, tall bars correspond to the same moments that produce spikes in the damage graph. The rarity of large combo values suggests that maintaining momentum is difficult, which is good for preserving challenge. At the same time, the presence of steady counts at **x2**, **x3**, and **x4**, plus the outlier at **x15**, proves that the system can generate both consistent incremental payoff and rare high-impact moments instead of keeping every battle outcome flat.

---

## Full Statistics View

![Full Statistics](full_statistics.png)

The full statistics screen combines the four core charts into one panel beside the inventory UI. This layout supports quick visual comparison across combat performance dimensions: damage output, pacing, typing efficiency, and streak building. Because the charts are shown together, the player can easily connect patterns such as slow solves leading to low combo, or strong combo runs producing damage spikes.

The design is effective because each chart focuses on a different layer of player performance. `Damage per Turn` measures output, `Time Taken per Word` measures pacing, `Keystrokes per Word` measures input efficiency, and `Combo Achieved` measures momentum. Taken together, these visualizations turn raw gameplay logs into readable feedback for balancing combat and evaluating player skill progression.

---

## Data Collection Summary

| Source File | Records | Key Columns | Purpose |
|---|---:|---|---|
| `data/raw/gameplay_stats.csv` | 112 | `time_taken_per_word`, `attempts_per_word`, `combo_achieved`, `damage_per_turn`, `keystrokes_per_word` | Stores combat-word performance logs used by the statistics UI |

---

## Interpretation Summary

The current visualization set shows that Cryptic Combat already captures the most important signals for a word-combat game: **speed**, **accuracy pressure**, **input efficiency**, **streak momentum**, and **damage payoff**. The updated data suggests that most logged combat actions are still low-combo turns, but the larger sample now shows more consistent mid-range combo and damage values than before. That balance is desirable because it keeps routine turns readable while preserving high-impact moments that make the combat feel rewarding.
