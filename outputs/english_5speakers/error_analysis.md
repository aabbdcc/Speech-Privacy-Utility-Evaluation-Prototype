# Recognition Error Case Analysis

Listener feedback, when available, is stored separately in listening_notes.md so regeneration does not overwrite it.

Scoring rule: `english_mr_mister_v1`. Existing CSV transcripts were rescored without rerunning inference.

Cases use normalized utterance WER changes relative to the same utterance's original audio: the largest increase for each pitch direction;
the stable case minimizes the maximum absolute change across both directions. Ties are resolved by lexicographic utterance ID order.
One utterance may satisfy multiple rules; criteria are not changed to force distinct cases. All ranking values are in case_ranking.csv.

Notation: `[Substitution: reference → hypothesis]`, `[Deletion: reference]`, `[Insertion: hypothesis]`.
Word alignments are one minimum-edit alignment returned by jiwer; equally valid alternative alignments may exist.
This automated report describes text differences only. Listening observations are recorded separately; edit types do not establish acoustic causes.

## Largest WER increase after downward shifting: 2277-149896-0004

Speaker: 2277.
Downward-shift change: +71.43 percentage points; upward-shift change: +14.29 percentage points.

Reference text (normalized):

HOW WOULD THE PAPERS TALK ABOUT IT

### original

WER: 0.00%; substitutions: 0, deletions: 0, insertions: 0.

Recognized text:

HOW WOULD THE PAPERS TALK ABOUT IT

Annotated alignment:

HOW WOULD THE PAPERS TALK ABOUT IT

[Listen to audio](audio/2277-149896-0004_original.wav)

### pitch_-3

WER: 71.43%; substitutions: 5, deletions: 0, insertions: 0.

Recognized text:

HOW DID THE PAPER STOP THEM OUT

Annotated alignment:

HOW [Substitution: WOULD → DID] THE [Substitution: PAPERS TALK ABOUT IT → PAPER STOP THEM OUT]

[Listen to audio](audio/2277-149896-0004_pitch_-3.wav)

### pitch_+3

WER: 14.29%; substitutions: 1, deletions: 0, insertions: 0.

Recognized text:

HOW DID THE PAPERS TALK ABOUT IT

Annotated alignment:

HOW [Substitution: WOULD → DID] THE PAPERS TALK ABOUT IT

[Listen to audio](audio/2277-149896-0004_pitch_+3.wav)

## Largest WER increase after upward shifting: 1988-147956-0004

Speaker: 1988.
Downward-shift change: +18.18 percentage points; upward-shift change: +40.91 percentage points.

Reference text (normalized):

PRESENTLY AGAINST ONE OF THOSE BANKS I SAW A SORT OF SHED THATCHED WITH THE SAME WINE COLORED GRASS THAT GREW EVERYWHERE

### original

WER: 0.00%; substitutions: 0, deletions: 0, insertions: 0.

Recognized text:

PRESENTLY AGAINST ONE OF THOSE BANKS I SAW A SORT OF SHED THATCHED WITH THE SAME WINE COLORED GRASS THAT GREW EVERYWHERE

Annotated alignment:

PRESENTLY AGAINST ONE OF THOSE BANKS I SAW A SORT OF SHED THATCHED WITH THE SAME WINE COLORED GRASS THAT GREW EVERYWHERE

[Listen to audio](audio/1988-147956-0004_original.wav)

### pitch_-3

WER: 18.18%; substitutions: 3, deletions: 0, insertions: 1.

Recognized text:

SUDDENLY AGAINST ONE OF THOSE BANKS I SAW A SORT OF SHED THAT I SHOOT THE SAME WINE COLORED GRASS THAT GREW EVERYWHERE

Annotated alignment:

[Substitution: PRESENTLY → SUDDENLY] AGAINST ONE OF THOSE BANKS I SAW A SORT OF SHED [Insertion: THAT] [Substitution: THATCHED WITH → I SHOOT] THE SAME WINE COLORED GRASS THAT GREW EVERYWHERE

[Listen to audio](audio/1988-147956-0004_pitch_-3.wav)

### pitch_+3

WER: 40.91%; substitutions: 6, deletions: 2, insertions: 1.

Recognized text:

FINALLY AGAINST ONE OF THOSE BANKS I SAW SOME SHED BASHED WITH THE SAME WINE COLORED GRASS IN THE LIVING ROOM

Annotated alignment:

[Substitution: PRESENTLY → FINALLY] AGAINST ONE OF THOSE BANKS I SAW [Substitution: A → SOME] [Deletion: SORT OF] SHED [Substitution: THATCHED → BASHED] WITH THE SAME WINE COLORED GRASS [Insertion: IN] [Substitution: THAT GREW EVERYWHERE → THE LIVING ROOM]

[Listen to audio](audio/1988-147956-0004_pitch_+3.wav)

## Smallest WER change across both directions: 2277-149896-0001

Speaker: 2277.
Downward-shift change: +3.85 percentage points; upward-shift change: +0.00 percentage points.

Reference text (normalized):

HE WOULD HAVE TO PAY HER THE MONEY WHICH SHE WOULD NOW REGULARLY DEMAND OR THERE WOULD BE TROUBLE IT DID NOT MATTER WHAT HE DID

### original

WER: 0.00%; substitutions: 0, deletions: 0, insertions: 0.

Recognized text:

HE WOULD HAVE TO PAY HER THE MONEY WHICH SHE WOULD NOW REGULARLY DEMAND OR THERE WOULD BE TROUBLE IT DID NOT MATTER WHAT HE DID

Annotated alignment:

HE WOULD HAVE TO PAY HER THE MONEY WHICH SHE WOULD NOW REGULARLY DEMAND OR THERE WOULD BE TROUBLE IT DID NOT MATTER WHAT HE DID

[Listen to audio](audio/2277-149896-0001_original.wav)

### pitch_-3

WER: 3.85%; substitutions: 1, deletions: 0, insertions: 0.

Recognized text:

HE WOULD HAVE TO PAY HER THE MONEY WHICH SHE WOULD NOW REGULARLY DEMAND OR THERE WOULD BE TROUBLE IT WOULD NOT MATTER WHAT HE DID

Annotated alignment:

HE WOULD HAVE TO PAY HER THE MONEY WHICH SHE WOULD NOW REGULARLY DEMAND OR THERE WOULD BE TROUBLE IT [Substitution: DID → WOULD] NOT MATTER WHAT HE DID

[Listen to audio](audio/2277-149896-0001_pitch_-3.wav)

### pitch_+3

WER: 0.00%; substitutions: 0, deletions: 0, insertions: 0.

Recognized text:

HE WOULD HAVE TO PAY HER THE MONEY WHICH SHE WOULD NOW REGULARLY DEMAND OR THERE WOULD BE TROUBLE IT DID NOT MATTER WHAT HE DID

Annotated alignment:

HE WOULD HAVE TO PAY HER THE MONEY WHICH SHE WOULD NOW REGULARLY DEMAND OR THERE WOULD BE TROUBLE IT DID NOT MATTER WHAT HE DID

[Listen to audio](audio/2277-149896-0001_pitch_+3.wav)
