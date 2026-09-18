# Speech Privacy–Utility Evaluation Prototype

**Completed experiment:** 25 English utterances from five speakers, evaluated
under original audio and ±3-semitone pitch shifts. Corpus WER was 1.62%, 14.80%
(+3), and 23.65% (-3). Speaker-reference comparisons and three qualitative
listening cases accompany the quantitative results.

Start with the [final experimental report](REPORT.md) for methods, results,
interpretation, and limitations. The [experiment log](EXPERIMENT_LOG.md) records
the debugging and methodological changes; instructions below explain how to run
the pipeline.

A small exploratory project examining a central question in privacy-preserving
speech processing:

> Can we reduce information captured by a pretrained speaker representation
> while preserving the linguistic content of the speech?

This repository is intentionally a **small evaluation prototype**, not a
validated voice-anonymisation system.

See the [experiment log](EXPERIMENT_LOG.md) for the observed failures, fixes,
speaker-sampling correction, completed runs, and the post-hoc MR/MISTER scoring
revision. The log was reconstructed from the session and saved outputs on
2026-09-19; it also identifies missing provenance and work not yet completed.

## Why this project?

Privacy-preserving speech systems face a trade-off: transformations that make a
speaker harder to identify can also damage linguistic, paralinguistic, or
clinically relevant information.

This prototype evaluates that trade-off on a small public speech sample by
comparing:

- **linguistic utility**: automatic speech recognition Word Error Rate (WER);
- **speaker-representation change**: cosine similarity between ECAPA-TDNN
  speaker embeddings before and after transformation.

Lower WER is better for linguistic utility. Lower original-to-transformed
speaker-embedding similarity indicates a larger change in the representation,
but **does not constitute a formal privacy guarantee**.

## Pipeline

```text
Public LibriSpeech samples
        |
        +--> Whisper ASR ----------------------> WER
        |
        +--> ECAPA-TDNN speaker embedding -----+
        |                                      |
        +--> exploratory pitch transformation  |
                     |                         |
                     +--> Whisper ASR ----------+--> utility comparison
                     |
                     +--> ECAPA-TDNN ------------> embedding similarity
```

## Models and data

- Dataset: `hf-internal-testing/librispeech_asr_dummy` (small LibriSpeech subset)
- ASR: `openai/whisper-base.en`
- Speaker representation: `speechbrain/spkrec-ecapa-voxceleb`
- Transformation: pitch shifting with `librosa`

The pitch shift is used only as a convenient experimental perturbation. It
should not be described as a validated anonymisation algorithm.

## Quick start

Python 3.10 or 3.11 is recommended.

### 1. Create an environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The script reads dataset audio with SoundFile and resamples it with librosa.
This loading path does not require TorchCodec/FFmpeg.

### 2. Run the MVP

```bash
python run_experiment.py --n-samples 12
```

For a faster CPU smoke test:

```bash
python run_experiment.py --n-samples 3 --pitch-steps 3
```

If CUDA is available:

```bash
python run_experiment.py --n-samples 12 --device cuda
```

## Outputs

### Multiple English speakers

```powershell
python run_experiment.py --n-speakers 5 --per-speaker 5 --pitch-steps -3 3 --device cpu --save-audio 25 --output-dir outputs/english_5speakers
```

This uses `openslr/librispeech_asr`, configuration `clean`, split `validation`,
streamed with audio decoding disabled and read using SoundFile. It selects the
first five encountered speakers and the first five utterances from each; this
is a convenience sample, not a random or demographically balanced sample.
These are English audiobook readings, not conversational or clinical recordings.
The script checks the requested counts before inference and saves the exact
utterance IDs in `sample_manifest.csv`. `per_speaker_summary.csv` reports each
speaker separately. WER is averaged over utterances with the same normalization
as the initial experiment (including counting MR/MISTER spelling differences).
Original and transformed audio are saved for the requested number of samples.
Results are checkpointed after each utterance; the summary and plot appear only
after the full run completes. This output directory preserves the earlier run.

The script produces:

```text
outputs/
├── results.csv
├── summary.csv
├── privacy_utility.png
└── audio/
```

`results.csv` contains one row per utterance and experimental condition.

`summary.csv` contains mean/median WER and speaker-embedding similarity for
each condition.

## Questions to analyse

Offline corpus WER and reproducibly selected error cases are available in
[the case report](outputs/english_5speakers/error_analysis.md) and
[the corpus summary](outputs/english_5speakers/corpus_summary.csv).
Regenerate them with:

```powershell
python analyze_results.py outputs/english_5speakers/results.csv
```

The script aligns each utterance separately with jiwer, then sums substitutions,
deletions, and insertions and divides by the total reference word count. It
reports both legacy and title-normalized scores alongside utterance means.
Case selection uses normalized WER changes from each utterance's original:
maximum increase for each pitch direction, and minimum worst absolute change
across both directions. Ties use utterance ID order. Cases are illustrative,
not a representative estimate; the full ranking is saved for audit.

### Abbreviation-aware scoring

After every completed run, `rescore_results.py` also produces
`results_normalized.csv`, `summary_normalized.csv`,
`per_speaker_summary_normalized.csv`, and `normalization_changes.csv`.
The scoring rule `english_mr_mister_v1` applies the same uppercase/punctuation/
whitespace normalization to references and hypotheses, then maps the exact
token `MR` (including punctuated `Mr.`) to `MISTER`. No other abbreviations,
names, or spelling variants are equated; `DR` and `ST` remain unchanged because
their expansion can depend on context. This rule assumes English titles in
the current audiobook material; it is not a universal abbreviation expander.

Legacy `wer`, reference/transcript columns, original CSV files, and the original
plot remain unchanged. The additional `wer_normalized` score and normalized
text columns allow direct auditing; `normalization_changes.csv` contains only
rows whose score changed. Summary scores are utterance means, not corpus WER.
This rule was added after inspecting errors, so report both scores.

Rescore saved transcripts without downloading data or running models:

```powershell
python rescore_results.py outputs/results.csv outputs/english_5speakers/results.csv
```

1. How much does each transformation increase WER?
2. How much does it reduce original-to-transformed speaker embedding similarity?
3. Is there a condition that changes the speaker representation substantially
   while preserving transcription quality?
4. Are results consistent across utterances/speakers?
5. Which conclusions are *not* justified by this experiment?

## Important limitations

Speaker-similarity reference groups can be regenerated offline from the saved
WAVs and local model files:

```powershell
python compare_speakers.py outputs/english_5speakers
```

The comparison includes all 50 unordered same-speaker/different-utterance pairs,
250 different-speaker pairs, and 25 same-utterance pairs for each pitch direction.
Self-pairs and duplicate reversed pairs are excluded from the original-audio
reference groups. Saved-WAV embeddings are recomputed for all conditions, and
differences from the earlier in-memory transformation scores are saved separately.
The pair table, descriptive quantiles, embeddings, and distribution plot are
stored beside the experimental results. Pairs share utterances and speakers and
are not independent observations. No verification threshold or privacy guarantee
is derived; original-to-original controls also differ in linguistic content from
the matched original-to-transformed comparisons.

### Observations from the completed English run

On 25 utterances from five speakers, corpus WER was 1.62% for original audio,
14.80% after +3 semitones, and 23.65% after -3 semitones. Both transformations
increased mean utterance WER for every sampled speaker; the relative effect of
pitch direction varied by speaker. Mean original-to-transformed embedding
similarity was 0.253 for +3 and 0.194 for -3; these values do not establish
anonymization success.

Using saved WAVs, the same-speaker/different-utterance reference mean was 0.762
(50 pairs), versus 0.143 for different speakers (250 pairs). Transformed scores
overlapped part of the different-speaker range and were below this sample's
same-speaker reference range. This is descriptive evidence of representation
change under the current model, not an evaluated privacy guarantee.
See the [reference distribution](outputs/english_5speakers/speaker_similarity_reference.png).

Exploratory feedback from one listener on three metric-selected cases described
reduced clarity and greater listening effort, including in a case with little
ASR error. The listener had reference-text or original-audio cues, so this is
qualitative feedback rather than a blinded intelligibility evaluation. Low ASR
WER alone did not capture all reported listening difficulties in these cases.
See the [listening notes](outputs/english_5speakers/listening_notes.md) for exact
observations and their limits.

This is an exploratory prototype.

- Pitch shifting is not a robust speaker-anonymisation method.
- Embedding cosine similarity is only a proxy for speaker information.
- A proper privacy evaluation would use speaker-verification attack metrics
  such as EER/linkability and potentially stronger attackers.
- Clinical utility cannot be inferred from LibriSpeech transcription quality.
  Clinical speech may contain prosodic, acoustic, or pathological biomarkers
  that ASR WER does not measure.
- The sample is deliberately small and intended for methodology exploration,
  not statistical claims.

These limitations are part of the project: they motivate a more rigorous
privacy–utility evaluation framework.
