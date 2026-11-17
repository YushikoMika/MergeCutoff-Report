#!/usr/bin/env bash
# Reproduces the whole experiment. Run from the project root:  bash scripts/run_all.sh
# Optional: TRIALS=3 bash scripts/run_all.sh   (quick smoke run, writes results/smoke.csv)
set -euo pipefail
cd "$(dirname "$0")/.."

SRC=src/main/java/MergeCutoff
OUT=out
mkdir -p "$OUT" data results

echo "== Machine info =="
{
  echo "date: $(date)"
  lscpu | grep "Model name" || true
  free -h | head -2
  uname -sr
  java -version 2>&1
} | tee results/machine_info.txt

echo "== Compile =="
javac -d "$OUT" "$SRC"/*.java

echo "== Correctness test (plain Java, no Maven needed) =="
if [ -f src/test/java/MergeCutoff/MergeSortMain.java ]; then
  javac -cp "$OUT" -d "$OUT" src/test/java/MergeCutoff/MergeSortMain.java
  java -cp "$OUT" MergeCutoff.MergeSortMain
else
  echo "(no plain-Java test found; run 'mvn test' separately)"
fi

echo "== Generate datasets (fixed seed) =="
java -cp "$OUT" MergeCutoff.DataGenerator data

echo "== Benchmark =="
if [ -n "${TRIALS:-}" ]; then
  java -Xms2g -Xmx2g -cp "$OUT" MergeCutoff.Benchmark data results/smoke.csv "$TRIALS"
  RAW=results/smoke.csv
else
  java -Xms2g -Xmx2g -cp "$OUT" MergeCutoff.Benchmark data results/raw.csv
  RAW=results/raw.csv
fi

echo "== Analysis and plots =="
python3 scripts/analyze.py "$RAW" results

echo "Done. See results/ (summary.csv, best_cutoff.csv, summary_tables.md, plot_*.png)."
