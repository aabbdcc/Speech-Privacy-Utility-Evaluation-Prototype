from __future__ import annotations

import argparse
from io import BytesIO
import re
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import soundfile as sf
import torch
import torch.nn.functional as F
from datasets import Audio, load_dataset
from jiwer import wer
from speechbrain.inference.speaker import SpeakerRecognition
from speechbrain.utils.fetching import LocalStrategy
from transformers import pipeline
from rescore_results import rescore_results


DATASET_NAME = "hf-internal-testing/librispeech_asr_dummy"
ASR_MODEL = "openai/whisper-base.en"
SPEAKER_MODEL = "speechbrain/spkrec-ecapa-voxceleb"
TARGET_SR = 16_000


def normalize_text(text: str) -> str:
    text = text.upper().strip()
    text = re.sub(r"[^A-Z0-9' ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def audio_to_numpy(audio_item) -> tuple[np.ndarray, int]:
    """
    Supports encoded audio, AudioDecoder objects, and legacy array dictionaries.
    """
    if hasattr(audio_item, "get_all_samples"):
        samples = audio_item.get_all_samples()
        wav = samples.data
        sr = int(samples.sample_rate)

        if isinstance(wav, torch.Tensor):
            wav = wav.detach().cpu().numpy()

        wav = np.asarray(wav, dtype=np.float32)
        if wav.ndim == 2:
            wav = wav.mean(axis=0)
        return wav.reshape(-1), sr

    if isinstance(audio_item, dict):
        if "array" not in audio_item:
            source = (BytesIO(audio_item["bytes"])
                      if audio_item.get("bytes") is not None
                      else audio_item.get("path"))
            if source is None:
                raise ValueError("Audio sample has neither bytes nor a file path.")
            wav, sr = sf.read(source, dtype="float32", always_2d=True)
            return wav.mean(axis=1), int(sr)
        wav = np.asarray(audio_item["array"], dtype=np.float32)
        sr = int(audio_item["sampling_rate"])
        if wav.ndim == 2:
            wav = wav.mean(axis=0)
        return wav.reshape(-1), sr

    raise TypeError(f"Unsupported audio type: {type(audio_item)}")


def ensure_16k(wav: np.ndarray, sr: int) -> np.ndarray:
    if sr != TARGET_SR:
        wav = librosa.resample(wav, orig_sr=sr, target_sr=TARGET_SR)
    return np.asarray(wav, dtype=np.float32)


def transform_audio(wav: np.ndarray, sr: int, n_steps: float) -> np.ndarray:
    """
    Exploratory transformation only. This is NOT claimed to be a validated
    anonymisation algorithm.
    """
    transformed = librosa.effects.pitch_shift(
        wav,
        sr=sr,
        n_steps=n_steps,
    )
    return np.asarray(transformed, dtype=np.float32)


def get_embedding(model: SpeakerRecognition, wav: np.ndarray) -> torch.Tensor:
    tensor = torch.tensor(wav, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        emb = model.encode_batch(tensor)
    return emb.squeeze().detach().cpu()


def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(F.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0)).item())


def load_sample(n_samples: int):
    ds = load_dataset(DATASET_NAME, split="validation")
    # Decode with SoundFile; ensure_16k handles resampling after loading.
    ds = ds.cast_column("audio", Audio(decode=False))

    # Keep the project small while trying to include more than one speaker
    # when speaker_id is available.
    if "speaker_id" not in ds.column_names:
        return ds.select(range(min(n_samples, len(ds))))

    selected = []
    seen_per_speaker = {}
    for idx, spk in enumerate(ds["speaker_id"]):
        if seen_per_speaker.get(spk, 0) < 4:
            selected.append(idx)
            seen_per_speaker[spk] = seen_per_speaker.get(spk, 0) + 1
        if len(selected) >= n_samples:
            break

    if len(selected) < n_samples:
        for idx in range(len(ds)):
            if idx not in selected:
                selected.append(idx)
            if len(selected) >= n_samples:
                break

    return ds.select(selected[:n_samples])


def build_models(device: str):
    if device == "auto":
        use_cuda = torch.cuda.is_available()
    else:
        use_cuda = device == "cuda"

    pipe_device = 0 if use_cuda else -1
    asr = pipeline(
        "automatic-speech-recognition",
        model=ASR_MODEL,
        device=pipe_device,
    )

    speaker = SpeakerRecognition.from_hparams(
        source=SPEAKER_MODEL,
        savedir="pretrained_models/spkrec-ecapa-voxceleb",
        local_strategy=LocalStrategy.COPY,
        run_opts={"device": "cuda" if use_cuda else "cpu"},
    )
    return asr, speaker


def load_multispeaker(n_speakers: int, per_speaker: int):
    ds = load_dataset("openslr/librispeech_asr", "clean", split="validation", streaming=True)
    ds = ds.cast_column("audio", Audio(decode=False))
    groups = {}
    for item in ds:
        spk = item["speaker_id"]
        if spk not in groups:
            if len(groups) >= n_speakers:
                continue
            groups[spk] = []
        if len(groups[spk]) < per_speaker:
            groups[spk].append(item)
        if len(groups) == n_speakers and all(len(v) == per_speaker for v in groups.values()):
            break
    if len(groups) != n_speakers or any(len(v) != per_speaker for v in groups.values()):
        raise ValueError("Dataset cannot satisfy the requested speaker/sample counts.")
    return [item for group in groups.values() for item in group]


def transcribe(asr, wav: np.ndarray, sr: int) -> str:
    result = asr({"raw": wav, "sampling_rate": sr})
    return result["text"].strip()


def make_plot(summary: pd.DataFrame, out_path: Path):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(summary["speaker_cosine_mean"], summary["wer_mean"], s=90)

    for _, row in summary.iterrows():
        ax.annotate(
            row["condition"],
            (row["speaker_cosine_mean"], row["wer_mean"]),
            xytext=(5, 5),
            textcoords="offset points",
        )

    ax.set_xlabel("Mean original↔transformed speaker embedding cosine similarity\n(lower = larger identity-representation change)")
    ax.set_ylabel("Mean ASR WER vs reference\n(lower = better linguistic utility)")
    ax.set_title("Exploratory privacy–utility trade-off")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=12)
    parser.add_argument("--n-speakers", type=int, default=0,
                        help="Use LibriSpeech clean validation with this many speakers; 0 uses dummy data.")
    parser.add_argument("--per-speaker", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--pitch-steps", type=float, nargs="+", default=[-3.0, 3.0])
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--save-audio", type=int, default=3,
                        help="Save transformed WAVs for the first N samples.")
    args = parser.parse_args()
    if args.n_speakers < 0 or args.per_speaker < 1 or args.n_samples < 1:
        parser.error("Sample counts must be positive and n-speakers must be nonnegative.")

    out_dir = args.output_dir
    audio_dir = out_dir / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(exist_ok=True)

    print("Loading sample dataset...")
    ds = (load_multispeaker(args.n_speakers, args.per_speaker)
          if args.n_speakers else load_sample(args.n_samples))
    print(f"Loaded {len(ds)} utterances.")
    manifest = pd.DataFrame([{"utterance_id": x["id"], "speaker_id": x["speaker_id"]} for x in ds])
    manifest.to_csv(out_dir / "sample_manifest.csv", index=False)
    print("Utterances per speaker:")
    print(manifest.groupby("speaker_id").size().to_string())

    print("Loading ASR and speaker models...")
    asr, speaker_model = build_models(args.device)

    rows = []

    for i, item in enumerate(ds):
        wav, sr = audio_to_numpy(item["audio"])
        wav = ensure_16k(wav, sr)
        sr = TARGET_SR

        ref = normalize_text(item["text"])
        spk = item.get("speaker_id", "unknown")
        utt_id = item.get("id", f"sample_{i:03d}")

        print(f"[{i+1}/{len(ds)}] {utt_id}")
        if i < args.save_audio:
            sf.write(audio_dir / f"{utt_id}_original.wav", wav, sr)

        original_transcript = normalize_text(transcribe(asr, wav, sr))
        original_wer = wer(ref, original_transcript)
        original_emb = get_embedding(speaker_model, wav)

        rows.append(
            {
                "utterance_id": utt_id,
                "speaker_id": spk,
                "condition": "original",
                "reference": ref,
                "transcript": original_transcript,
                "wer": original_wer,
                "speaker_cosine_to_original": 1.0,
            }
        )

        for n_steps in args.pitch_steps:
            condition = f"pitch_{n_steps:+g}"
            transformed = transform_audio(wav, sr, n_steps=n_steps)

            transformed_transcript = normalize_text(
                transcribe(asr, transformed, sr)
            )
            transformed_wer = wer(ref, transformed_transcript)
            transformed_emb = get_embedding(speaker_model, transformed)
            similarity = cosine_similarity(original_emb, transformed_emb)

            rows.append(
                {
                    "utterance_id": utt_id,
                    "speaker_id": spk,
                    "condition": condition,
                    "reference": ref,
                    "transcript": transformed_transcript,
                    "wer": transformed_wer,
                    "speaker_cosine_to_original": similarity,
                }
            )

            if i < args.save_audio:
                sf.write(
                    audio_dir / f"{utt_id}_{condition}.wav",
                    transformed,
                    sr,
                )

        pd.DataFrame(rows).to_csv(out_dir / "results.csv", index=False)

    results = pd.DataFrame(rows)
    results.to_csv(out_dir / "results.csv", index=False)

    summary = (
        results.groupby("condition", as_index=False)
        .agg(
            n=("utterance_id", "count"),
            wer_mean=("wer", "mean"),
            wer_median=("wer", "median"),
            speaker_cosine_mean=("speaker_cosine_to_original", "mean"),
            speaker_cosine_median=("speaker_cosine_to_original", "median"),
        )
        .sort_values("condition")
    )
    summary.to_csv(out_dir / "summary.csv", index=False)
    results.groupby(["speaker_id", "condition"]).agg(
        n=("utterance_id", "count"), wer_mean=("wer", "mean"),
        speaker_cosine_mean=("speaker_cosine_to_original", "mean"),
    ).to_csv(out_dir / "per_speaker_summary.csv")

    make_plot(summary, out_dir / "privacy_utility.png")
    rescore_results(out_dir / "results.csv")

    print("\nSummary")
    print(summary.to_string(index=False))
    print("\nSaved:")
    print(f"  {out_dir.resolve()}")
    print("\nInterpretation:")
    print("- Lower WER = better linguistic utility.")
    print("- Lower original-to-transformed cosine similarity = larger change in")
    print("  the pretrained speaker representation.")
    print("- Cosine similarity here is ONLY an exploratory privacy proxy;")
    print("  it is not a calibrated privacy guarantee or anonymisation metric.")


if __name__ == "__main__":
    main()
