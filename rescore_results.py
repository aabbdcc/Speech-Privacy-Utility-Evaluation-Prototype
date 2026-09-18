"""Add an explicit English title-normalized WER without changing legacy scores."""

import argparse
from pathlib import Path
import re

import pandas as pd
from jiwer import wer


SCORING_RULE = "english_mr_mister_v1"


def normalize_for_scoring(text: str) -> str:
    text = text.upper().strip()
    text = re.sub(r"[^A-Z0-9' ]+", " ", text)
    # Exact tokens only: MR/MR. are equivalent to MISTER in these English readings.
    # Do not expand ambiguous titles such as DR or ST, or alter names.
    return " ".join("MISTER" if token == "MR" else token for token in text.split())


def rescore_results(path: Path) -> pd.DataFrame:
    results = pd.read_csv(path, keep_default_na=False)
    results["scoring_rule"] = SCORING_RULE
    results["reference_normalized"] = results["reference"].map(normalize_for_scoring)
    results["transcript_normalized"] = results["transcript"].map(normalize_for_scoring)
    results["wer_normalized"] = [
        wer(ref, hyp) for ref, hyp in zip(
            results["reference_normalized"], results["transcript_normalized"]
        )
    ]
    results["wer_change"] = results["wer_normalized"] - results["wer"]
    results.to_csv(path.with_name("results_normalized.csv"), index=False)
    results.loc[results["wer_change"].abs() > 1e-12].to_csv(
        path.with_name("normalization_changes.csv"), index=False
    )
    summary = None
    for keys, filename in [
        (["condition"], "summary_normalized.csv"),
        (["speaker_id", "condition"], "per_speaker_summary_normalized.csv"),
    ]:
        table = results.groupby(keys, as_index=False).agg(
            n=("utterance_id", "count"),
            wer_mean=("wer", "mean"),
            wer_normalized_mean=("wer_normalized", "mean"),
            wer_normalized_median=("wer_normalized", "median"),
            speaker_cosine_mean=("speaker_cosine_to_original", "mean"),
        )
        table.to_csv(path.with_name(filename), index=False)
        if keys == ["condition"]:
            summary = table
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, nargs="+")
    args = parser.parse_args()
    for path in args.results:
        print(path)
        print(rescore_results(path).to_string(index=False))
