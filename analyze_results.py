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
        ("降调 WER 增幅最大", ranking.sort_values(["delta_minus3", "utterance_id"], ascending=[False, True]).iloc[0]),
        ("升调 WER 增幅最大", ranking.sort_values(["delta_plus3", "utterance_id"], ascending=[False, True]).iloc[0]),
        ("两种变调的 WER 变化最小", ranking.sort_values(["max_absolute_delta", "utterance_id"]).iloc[0]),
    ]
    lines = ["# 识别错误案例分析", "", "人工试听反馈另见 listening_notes.md（如已记录），独立保存以避免被本报告覆盖。", "", f"评分规则：`{SCORING_RULE}`。从现有 CSV 重新评分，没有重新推理。",
             "", "按每句标准化 WER 相对该句原始音频的变化选例：降调/升调分别取增幅最大；",
             "稳定案例取两种变调的绝对变化中的最大值最小者。并列按音频 ID 字典序选取。",
             "同一句可以符合多个规则，不为凑不同案例改变选取标准。完整排序指标见 case_ranking.csv。",
             "", "标记：`[替换: 参考 → 识别]`、`[删除: 参考]`、`[插入: 识别]`。",
             "词级对齐为 jiwer 给出的一种最小编辑对齐；有多个等价对齐时并非唯一解释。",
             "本报告只说明文本差异；没有进行人工试听，也不把替换类型当成声学原因。", ""]
    for title, selected in selections:
        uid = selected.utterance_id
        group = data[data.utterance_id == uid].set_index("condition")
        lines += [f"## {title}：{uid}", "", f"说话人：{group.iloc[0].speaker_id}。",
                  f"降调变化：{selected.delta_minus3*100:+.2f} 个百分点；升调变化：{selected.delta_plus3*100:+.2f} 个百分点。", "",
                  "参考文本（标准化后）：", "", normalize_for_scoring(group.iloc[0].reference), ""]
        for condition in ("original", "pitch_-3", "pitch_+3"):
            row = group.loc[condition]
            ref, hyp = normalize_for_scoring(row.reference), normalize_for_scoring(row.transcript)
            result = process_words(ref, hyp)
            marked = []
            for chunk in result.alignments[0]:
                r = " ".join(result.references[0][chunk.ref_start_idx:chunk.ref_end_idx])
                h = " ".join(result.hypotheses[0][chunk.hyp_start_idx:chunk.hyp_end_idx])
                marked.append(h if chunk.type == "equal" else
                              f"[替换: {r} → {h}]" if chunk.type == "substitute" else
                              f"[删除: {r}]" if chunk.type == "delete" else f"[插入: {h}]")
            lines += [f"### {condition}", "", f"WER：{result.wer:.2%}；替换 {result.substitutions}、删除 {result.deletions}、插入 {result.insertions}。",
                      "", "识别文本：", "", hyp, "", "对齐标记：", "", " ".join(marked), ""]
            audio = path.parent / "audio" / f"{uid}_{condition}.wav"
            if audio.exists():
                lines += [f"[试听音频](audio/{audio.name})", ""]
    path.with_name("error_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    return totals


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    print(analyze(args.results).to_string(index=False))
