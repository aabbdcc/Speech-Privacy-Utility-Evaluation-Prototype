"""Compare descriptive speaker-similarity distributions using saved WAVs."""

import argparse
from itertools import combinations
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import soundfile as sf
from speechbrain.inference.speaker import SpeakerRecognition
from speechbrain.utils.fetching import LocalStrategy

from run_experiment import get_embedding, cosine_similarity, TARGET_SR


def compare(folder: Path):
    os.environ["HF_HUB_OFFLINE"] = "1"
    manifest = pd.read_csv(folder / "sample_manifest.csv", dtype={"utterance_id": str})
    if manifest.utterance_id.duplicated().any():
        raise ValueError("Duplicate utterance IDs")
    model_dir = Path(__file__).parent / "pretrained_models/spkrec-ecapa-voxceleb"
    model = SpeakerRecognition.from_hparams(
        source=str(model_dir), savedir=str(model_dir),
        overrides={"pretrained_path": model_dir.as_posix()},
        local_strategy=LocalStrategy.COPY, run_opts={"device": "cpu"})
    embeddings = {}
    for i, item in manifest.iterrows():
        for condition in ("original", "pitch_-3", "pitch_+3"):
            wav, sr = sf.read(folder / "audio" / f"{item.utterance_id}_{condition}.wav", dtype="float32")
            if sr != TARGET_SR or wav.ndim != 1:
                raise ValueError("Expected saved mono 16 kHz audio")
            embeddings[(item.utterance_id, condition)] = get_embedding(model, wav)
        print(f"Embedded {i+1}/{len(manifest)} utterances", flush=True)
    keys = list(embeddings)
    np.savez(folder / "speaker_embeddings.npz",
             utterance_id=np.array([x[0] for x in keys]),
             condition=np.array([x[1] for x in keys]),
             embeddings=np.stack([embeddings[x].numpy() for x in keys]))
    pairs = []
    def add(a, b, condition, group):
        pairs.append(dict(group=group, utterance_a=a.utterance_id, speaker_a=a.speaker_id,
                          utterance_b=b.utterance_id, speaker_b=b.speaker_id,
                          condition_b=condition, similarity=cosine_similarity(
                              embeddings[(a.utterance_id, "original")], embeddings[(b.utterance_id, condition)])))
    records = list(manifest.itertuples(index=False))
    for a, b in combinations(records, 2):
        add(a, b, "original", "same_speaker" if a.speaker_id == b.speaker_id else "different_speaker")
    for a in records:
        for condition in ("pitch_-3", "pitch_+3"):
            add(a, a, condition, condition)
    pairs = pd.DataFrame(pairs)
    pairs.to_csv(folder / "speaker_similarity_pairs.csv", index=False)
    summary = pairs.groupby("group").similarity.agg(n="count", mean="mean", median="median", min="min", max="max")
    for name, q in (("q05", .05), ("q25", .25), ("q75", .75), ("q95", .95)):
        summary[name] = pairs.groupby("group").similarity.quantile(q)
    summary.to_csv(folder / "speaker_similarity_summary.csv")
    previous = pd.read_csv(folder / "results.csv")
    comparison = pairs[pairs.group.str.startswith("pitch_")].merge(
        previous, left_on=["utterance_a", "group"], right_on=["utterance_id", "condition"], validate="one_to_one")
    comparison["saved_wav_minus_prior"] = comparison.similarity - comparison.speaker_cosine_to_original
    comparison[["utterance_id", "condition", "speaker_cosine_to_original", "similarity", "saved_wav_minus_prior"]].to_csv(
        folder / "speaker_similarity_recheck.csv", index=False)
    order = ["same_speaker", "different_speaker", "pitch_-3", "pitch_+3"]
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, group in enumerate(order):
        values = pairs.loc[pairs.group == group, "similarity"].to_numpy()
        ax.scatter(i + np.random.default_rng(42+i).uniform(-.12, .12, len(values)), values, alpha=.4, s=15)
        ax.plot([i-.2, i+.2], [np.median(values)]*2, color="black", linewidth=2)
    ax.set_xticks(range(4), ["Same speaker\ndifferent utterances", "Different speakers\noriginal audio", "Original vs -3\nsame utterance", "Original vs +3\nsame utterance"])
    ax.set_ylabel("ECAPA embedding cosine similarity")
    ax.set_title("Five-speaker descriptive comparison (pairs are not independent)")
    ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    fig.savefig(folder / "speaker_similarity_reference.png", dpi=180)
    plt.close(fig)
    print(summary.to_string())
    print("Maximum absolute difference from prior in-memory scores:", comparison.saved_wav_minus_prior.abs().max())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    compare(parser.parse_args().folder)
