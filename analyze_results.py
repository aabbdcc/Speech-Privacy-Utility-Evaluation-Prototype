"""Compute corpus WER and select reproducible error-analysis cases offline."""

import argparse
from pathlib import Path

import pandas as pd
from jiwer import process_words

from rescore_results import normalize_for_scoring, SCORING_RULE


def analyze(path: Path):
    data = pd.read_csv(path, keep_default_na=False)
    if data.duplicated(["utterance_id", "condition"]).any():
        raise ValueError("Duplicate utterance/condition records")
    expected = set(data.loc[data.condition == "original", "utterance_id"])
    for _, group in data.groupby("condition"):
        if set(group.utterance_id) != expected:
            raise ValueError("Conditions must contain the same utterances")
    counts = []
    for row in data.to_dict("records"):
        for rule in ("legacy", SCORING_RULE):
            ref, hyp = row["reference"], row["transcript"]
            if rule != "legacy":
                ref, hyp = normalize_for_scoring(ref), normalize_for_scoring(hyp)
            result = process_words(ref, hyp)
            n = sum(map(len, result.references))
            counts.append(dict(utterance_id=row["utterance_id"], speaker_id=row["speaker_id"],
                               condition=row["condition"], scoring_rule=rule,
                               reference_words=n, substitutions=result.substitutions,
                               deletions=result.deletions, insertions=result.insertions,
                               wer=result.wer))
    scores = pd.DataFrame(counts)
    scores.to_csv(path.with_name("word_error_counts.csv"), index=False)
    totals = scores.groupby(["scoring_rule", "condition"], as_index=False).agg(
        n=("utterance_id", "count"), reference_words=("reference_words", "sum"),
        substitutions=("substitutions", "sum"), deletions=("deletions", "sum"),
        insertions=("insertions", "sum"), utterance_mean_wer=("wer", "mean"))
    totals["corpus_wer"] = (totals.substitutions + totals.deletions + totals.insertions) / totals.reference_words
    totals.to_csv(path.with_name("corpus_summary.csv"), index=False)

    normalized = scores[scores.scoring_rule == SCORING_RULE]
    wide = normalized.pivot(index="utterance_id", columns="condition", values="wer")
    ranking = pd.DataFrame(index=wide.index)
    ranking["delta_minus3"] = wide["pitch_-3"] - wide.original
    ranking["delta_plus3"] = wide["pitch_+3"] - wide.original
    # Stable means little change in BOTH directions, not merely one favorable condition.
    ranking["max_absolute_delta"] = ranking.abs().max(axis=1)
    ranking = ranking.reset_index()
    ranking.to_csv(path.with_name("case_ranking.csv"), index=False)
    selections = [
        ("Largest WER increase after downward shifting", ranking.sort_values(["delta_minus3", "utterance_id"], ascending=[False, True]).iloc[0]),
        ("Largest WER increase after upward shifting", ranking.sort_values(["delta_plus3", "utterance_id"], ascending=[False, True]).iloc[0]),
        ("Smallest WER change across both directions", ranking.sort_values(["max_absolute_delta", "utterance_id"]).iloc[0]),
    ]
    lines = ["# Recognition Error Case Analysis", "", "Listener feedback, when available, is stored separately in listening_notes.md so regeneration does not overwrite it.", "", f"Scoring rule: `{SCORING_RULE}`. Existing CSV transcripts were rescored without rerunning inference.",
             "", "Cases use normalized utterance WER changes relative to the same utterance's original audio: the largest increase for each pitch direction;",
             "the stable case minimizes the maximum absolute change across both directions. Ties are resolved by lexicographic utterance ID order.",
             "One utterance may satisfy multiple rules; criteria are not changed to force distinct cases. All ranking values are in case_ranking.csv.",
             "", "Notation: `[Substitution: reference → hypothesis]`, `[Deletion: reference]`, `[Insertion: hypothesis]`.",
             "Word alignments are one minimum-edit alignment returned by jiwer; equally valid alternative alignments may exist.",
             "This automated report describes text differences only. Listening observations are recorded separately; edit types do not establish acoustic causes.", ""]
    for title, selected in selections:
        uid = selected.utterance_id
        group = data[data.utterance_id == uid].set_index("condition")
        lines += [f"## {title}: {uid}", "", f"Speaker: {group.iloc[0].speaker_id}.",
                  f"Downward-shift change: {selected.delta_minus3*100:+.2f} percentage points; upward-shift change: {selected.delta_plus3*100:+.2f} percentage points.", "",
                  "Reference text (normalized):", "", normalize_for_scoring(group.iloc[0].reference), ""]
        for condition in ("original", "pitch_-3", "pitch_+3"):
            row = group.loc[condition]
            ref, hyp = normalize_for_scoring(row.reference), normalize_for_scoring(row.transcript)
            result = process_words(ref, hyp)
            marked = []
            for chunk in result.alignments[0]:
                r = " ".join(result.references[0][chunk.ref_start_idx:chunk.ref_end_idx])
                h = " ".join(result.hypotheses[0][chunk.hyp_start_idx:chunk.hyp_end_idx])
                marked.append(h if chunk.type == "equal" else
                              f"[Substitution: {r} → {h}]" if chunk.type == "substitute" else
                              f"[Deletion: {r}]" if chunk.type == "delete" else f"[Insertion: {h}]")
            lines += [f"### {condition}", "", f"WER: {result.wer:.2%}; substitutions: {result.substitutions}, deletions: {result.deletions}, insertions: {result.insertions}.",
                      "", "Recognized text:", "", hyp, "", "Annotated alignment:", "", " ".join(marked), ""]
            audio = path.parent / "audio" / f"{uid}_{condition}.wav"
            if audio.exists():
                lines += [f"[Listen to audio](audio/{audio.name})", ""]
    path.with_name("error_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    return totals


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    print(analyze(args.results).to_string(index=False))
