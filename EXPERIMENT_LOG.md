# Experiment Log

## About this record

This log was reconstructed on 2026-09-19 from the working conversation, terminal
outputs, and saved CSV files. It is not a preregistered protocol or a complete
timestamped execution trace. Unrecorded times, model revisions, and results have
not been invented. Future experiments should use the template at the end.

Research question: how does simple pitch shifting affect English transcription
quality and speaker representations? This is exploratory evaluation, not
validation of anonymization effectiveness or clinical utility.

Confirmed environment: Windows / PowerShell, project `.venv`, PyTorch
`2.14.0+cpu`, CPU inference. ASR: `openai/whisper-base.en`. Speaker model:
`speechbrain/spkrec-ecapa-voxceleb`. Audio was processed at 16 kHz with librosa
pitch shifting. Complete historical dependency snapshots and all model/data
revisions were not saved, so exact numerical reproduction cannot be claimed.

## 01 — Imports passed, but audio decoding failed

- **Observation:** Key dependencies imported successfully. In the one-sample run,
  data downloaded, but reading audio raised `RuntimeError: Could not load libtorchcodec`.
- **Diagnosis:** Import success did not establish that native decoding worked.
  The precise cause among FFmpeg availability, version compatibility, and other
  runtime dependencies was not isolated.
- **Change:** Use `Audio(decode=False)`, decode bytes or paths with SoundFile,
  and resample with librosa. Iterate only over speaker IDs during selection,
  avoiding premature decoding of all audio.
- **Verification:** The first cached sample decoded successfully: 16000 Hz and
  93680 samples. Later full inference also passed. No complete environment reinstall.

## 02 — SpeechBrain could not create Windows symlinks

- **Observation:** `WinError 1314` occurred when linking cached `hyperparams.yaml`
  into the project's `pretrained_models` directory.
- **Change:** Set `local_strategy=LocalStrategy.COPY` in
  `SpeakerRecognition.from_hparams`.
- **Verification:** A local copy check passed, followed by model loading and inference.
- **Trade-off:** Copying can increase disk usage. Administrator execution or
  changes to Windows Developer Mode were not required.

## 03 — One-utterance smoke test

```powershell
python run_experiment.py --n-samples 1 --pitch-steps 3 --device cpu --save-audio 1
```

- **Result:** Original and +3-semitone WER were both 0.058824. Transformed-to-original
  embedding similarity was 0.220883.
- **Interpretation:** The pipeline worked; one example cannot establish an aggregate
  trend. Cosine similarity is not an identification success rate.
- **Retention limitation:** These values come from the terminal record. The CSV was
  overwritten by the subsequent 12-utterance run and was not separately archived.

## 04 — Twelve-utterance pilot and speaker coverage

```powershell
python run_experiment.py --n-samples 12 --pitch-steps -3 3 --device cpu --save-audio 3
```

- **Results:** [Original summary](outputs/summary.csv) and [results](outputs/results.csv).
- **Observation:** All 12 utterances belonged to speaker `1272`. All 73 locally
  cached dummy examples also belonged to this speaker. The original sampler
  attempted a per-speaker cap but filled remaining slots afterward, so multiple
  speakers were not guaranteed.
- **Decision:** Change datasets and check speaker and utterance counts before
  inference; increasing `--n-samples` alone would not solve the problem.
- **Limit:** The pilot supports observations about one speaker, not effects across speakers.

## 05 — Five-speaker English experiment

```powershell
python run_experiment.py --n-speakers 5 --per-speaker 5 --pitch-steps -3 3 --device cpu --save-audio 25 --output-dir outputs/english_5speakers
```

- **Data:** `openslr/librispeech_asr`, `clean`, `validation`: English audiobook
  readings, not conversation or clinical speech.
- **Selection:** First five encountered speakers, first five utterances each:
  2277, 2035, 2086, 7976, 1988. Convenience sampling, not random or demographically balanced.
- **Controls:** Fail if requested counts cannot be met; save a manifest,
  per-speaker summaries, and original/transformed WAVs; checkpoint results after
  each utterance. A separate directory preserves the pilot.
- **Execution issues:** Initial network access was blocked by execution-environment
  permissions; rerun after approval. After artifacts were saved, `↔` in the final
  console explanation caused a GBK encoding error. Replace that console text with
  ASCII. Inference was not rerun for this post-save error.
- **Verification:** 25 unique IDs, five speakers, 75 condition records, five rows
  per speaker/condition, no missing values, 75 WAVs, and a nonempty plot.
- **Observation:** Both shifts increased mean WER for every speaker. Downward
  shifting was worse for four speakers; 2035 showed the reverse. The aggregate
  trend is not universal across speakers.
- **Artifacts:** [Manifest](outputs/english_5speakers/sample_manifest.csv),
  [results](outputs/english_5speakers/results.csv),
  [per-speaker summary](outputs/english_5speakers/per_speaker_summary.csv).

## 06 — Error inspection identified MR/MISTER scoring differences

- **Evidence:** Pilot `1272-128104-0001` had reference
  `NOR IS MISTER QUILTER'S MANNER LESS INTERESTING THAN HIS MATTER` and transcription
  `NOR IS MR QUILTER'S MANNER LESS INTERESTING THAN HIS MATTER`. Its 10% WER arose
  from the title abbreviation rather than a content difference for that word.
- **Change:** Add [rescore_results.py](rescore_results.py), rule
  `english_mr_mister_v1`. Apply identical case, punctuation, and whitespace
  processing to both texts, then map the exact token `MR` to `MISTER`, also handling `Mr.`.
- **Scope:** An English title rule, not universal abbreviation expansion. Do not
  merge `DR`, `ST`, names, or other spelling variants. `QUILTER` versus `COULTER` remains an error.
- **Verification:** Check equivalence in both directions, exact-token matching,
  idempotence, retention of genuine errors, and preservation of every original column.
- **Rescoring:** Read saved CSVs without inference. Preserve original CSVs and
  plots; save additional outputs. `normalization_changes.csv` lists changed scores.
- **Method:** This correction followed error inspection. Report both scores and
  apply the same rule to all speakers and conditions, without selective correction.

Utterance-mean WER percentages (not corpus WER):

| Data | Condition | Original scoring | MR/MISTER normalized |
| --- | --- | ---: | ---: |
| One speaker, 12 utterances | Original | 9.6943% | 7.0636% |
| One speaker, 12 utterances | +3 semitones | 22.4874% | 19.8567% |
| One speaker, 12 utterances | -3 semitones | 43.5037% | 41.7064% |
| Five speakers, 25 utterances | Original | 2.0748% | 2.0748% |
| Five speakers, 25 utterances | +3 semitones | 15.2101% | 15.2101% |
| Five speakers, 25 utterances | -3 semitones | 24.4309% | 24.4309% |

Sources: [pilot rescoring](outputs/summary_normalized.csv),
[multi-speaker rescoring](outputs/english_5speakers/summary_normalized.csv).
The rule changed some pilot scores but no main-experiment scores. Additional rules
should not be introduced merely to obtain lower scores.

## 07 — Corpus WER and rule-based case selection (2026-09-19)

- **Motivation:** Utterance means weight short and long sentences equally. Add
  corpus WER to check whether the trend depends on aggregation.
- **Implementation:** [analyze_results.py](analyze_results.py) aligns saved
  utterances separately with jiwer; corpus WER is total substitutions, deletions,
  and insertions divided by total reference words. No cross-sentence concatenation
  or model rerun; output both scoring rules.
- **Results:** Each condition has 554 reference words. Original: 9 errors, 1.6245%;
  +3: 82 errors, 14.8014%; -3: 131 errors, 23.6462%. Both text rules agree, as does
  the condition ordering under utterance means. See [corpus summary](outputs/english_5speakers/corpus_summary.csv).
- **Selection:** Largest normalized WER increase from the same utterance's original
  in each direction; stable case minimizes the maximum absolute change across
  directions. Ties use utterance ID order; the same utterance may satisfy multiple
  rules. This operational definition was not preregistered.
- **Cases:** Largest -3 increase: `2277-149896-0004` (0% to 71.43%, seven words);
  largest +3: `1988-147956-0004` (0% to 40.91%, 22 words); stable:
  `2277-149896-0001` (original 0%, -3 3.85%, +3 0%, 26 words).
- **Verification:** Check edit-count arithmetic and cross-check with jiwer on
  sentence lists. All ranking values are retained; audio links resolve to saved files.
- **Limits at this stage:** Extremes can favor short sentences and are not typical
  samples. Alignments may not be unique. Text analysis did not establish acoustic
  causes; listening had not yet been conducted.
- **Artifacts:** [Cases](outputs/english_5speakers/error_analysis.md),
  [word counts](outputs/english_5speakers/word_error_counts.csv),
  [ranking](outputs/english_5speakers/case_ranking.csv).

## 08 — Subjective listening: first case

- **Case:** `2277-149896-0004`, `HOW WOULD THE PAPERS TALK ABOUT IT`.
- **Conditions:** Reference text was known; both shifted versions were heard.
  No blinded procedure or independent transcription.
- **Initial observation:** Both remained understandable, but the opening around
  HOW, WOULD, and PAPERS was difficult to distinguish, especially WOULD. Initially
  there was no explicit original-audio comparison or distortion rating.
- **ASR comparison:** Both shifts changed WOULD to DID. This was the only +3
  substitution; -3 also changed PAPERS TALK ABOUT IT to PAPER STOP THEM OUT.
  Some subjective difficulty locations coincided with model errors.
- **Initial limit:** Familiarity assists recognition; this does not establish
  unchanged blinded comprehension or clinical utility. Whether shifting introduced
  the difficulty was initially unresolved.
- **Follow-up:** The user confirmed WOULD was clearer in the original. This
  suggests reduced clarity after shifting in this case, consistent with ASR errors.
  It updates the initially missing comparison but does not identify an acoustic
  mechanism or constitute a blinded test.
- **Next step at the time:** Listen to the other cases.

## 09 — Subjective listening: second case

- **Case:** `1988-147956-0004`, original versus upward shift.
- **Observation:** Harder to understand after shifting, becoming unclear from AGAINST onward.
- **Conditions:** The immediate prompt omitted the reference, but the earlier
  case report included it. Prior reading was not established; this is not controlled
  blind listening. No independent transcription score was collected.
- **ASR comparison:** Original WER 0%; +3 40.91%. AGAINST itself was correct;
  substitutions, deletions, and insertions occurred elsewhere. The perceived
  start of muddiness need not be an incorrectly recognized word.
- **Interpretation:** Subjective difficulty and ASR errors increased together,
  without word-for-word agreement or an established acoustic mechanism.
- **Next step at the time:** Listen to the stable case to check for disagreement
  between recognition performance and listening experience.

## 10 — Third case and listening synthesis

- **Case:** `2277-149896-0001`, original and both shifts.
- **Observation:** Unclear speech after PAY HER THE MONEY; more effort for the
  downward shift; understanding remained possible after hearing the original.
  The user's approximate location was "after pay her money", not an exact
  transcription or timestamp annotation.
- **ASR comparison:** Original and +3 WER 0%; -3 3.85%, only the later DID-to-WOULD
  substitution. Do not equate that error with the reported unclear region.
- **Interpretation:** Low ASR error can coexist with listening effort. Hearing the
  original provides a cue; unchanged first-exposure intelligibility cannot be inferred.
- **Completion:** Feedback for all three cases is in the
  [listening notes](outputs/english_5speakers/listening_notes.md). No formal listener study.

## 11 — Speaker-similarity reference groups

- **Purpose:** Provide within-sample context for similarity, without setting a verification threshold.
- **Implementation:** [compare_speakers.py](compare_speakers.py) loads local ECAPA
  files and extracts embeddings from 75 saved WAVs. No downloads or ASR rerun.
  Embeddings are saved for further analysis.
- **Pairs:** `5 × C(5,2) = 50` same-speaker/different-utterance pairs;
  `C(5,2) × 5 × 5 = 250` different-speaker pairs; 25 matched original/transformed
  pairs per direction. Reference groups exclude self-pairs and reversed duplicates.
- **Results:** Same speaker mean 0.761971, median 0.767050; different speakers mean
  0.143014, median 0.138973; -3 mean 0.194049, median 0.174716; +3 mean 0.253173,
  median 0.241169. Shifted scores are well below the same-speaker reference and
  partially overlap the different-speaker range.
- **Numerical check:** Saved-WAV scores differ from earlier in-memory scores by
  at most 0.000685. Retain both in a comparison table rather than overwrite old
  scores. Quantization and numerical computation may contribute; their individual
  contributions were not isolated.
- **Verification:** All 350 pairs passed count, identity-group, reference uniqueness,
  non-self-pair, and finite-score/range checks ([-1,1]). The plot was visually inspected.
- **Limits:** Five speakers only; pairs share samples and are not independent.
  Original controls contain different text, while transformed pairs share source
  utterances. No adapted attacker, separate enrollment/test protocol, or EER.
  Anonymization success cannot be claimed.
- **Artifacts:** [Summary](outputs/english_5speakers/speaker_similarity_summary.csv),
  [pairs](outputs/english_5speakers/speaker_similarity_pairs.csv),
  [plot](outputs/english_5speakers/speaker_similarity_reference.png),
  [numerical check](outputs/english_5speakers/speaker_similarity_recheck.csv).

## 12 — English experimental report

- **Artifact:** [REPORT.md](REPORT.md): research question, methods, scoring correction,
  aggregate and per-speaker results, similarity references, listening cases,
  limitations, and reproduction commands.
- **Presentation:** Add actual results and report entry point to README; remove
  the prewritten CV description.
- **Verification:** Check links, corpus WER, similarity means, and reference-word
  counts against saved files.
- **Scope:** No new experiments or claims of anonymization success. Retain the
  limitations of post-hoc scoring, single-listener nonblinded feedback, convenience
  sampling, and incomplete historical version information.

## Current outstanding work

Corpus WER, three text cases, exploratory listening, and similarity references
are complete. Formal listener and privacy-attack evaluations remain unimplemented.

- Save full run configurations, dependency snapshots, model/data revisions, and
  separate run directories.
- Classify additional recognition errors with explicit case-selection criteria.
- Formal privacy attacks, clinical utility, and multilingual evaluation have not
  been conducted.
- Current English processing removes Chinese characters and French accents.
  Language expansion requires new text rules and replacement of the English-only ASR.

## Template for future entries

```text
Date / experiment ID:
Question or hypothesis:
Evidence (error, utterance ID, file):
Settings specified before running (data version, samples, model, parameters, scoring rule):
Change and rationale:
Actual command:
Verification results and artifact paths:
Observations and interpretation (separate facts from hypotheses):
Limitations and next steps:
Was this a revision made after inspecting results?:
```
