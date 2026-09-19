# Subjective Listening Notes

Manual feedback is stored separately so regenerating the automated error report
does not overwrite it. The observations below are translated from feedback
provided in Chinese by one listener.

## 2026-09-19: 2277-149896-0004

Reference: HOW WOULD THE PAPERS TALK ABOUT IT

Knowing the reference text, the listener reported that both upward and downward
shifts remained understandable, but the opening around HOW, WOULD, and PAPERS
was harder to distinguish, especially WOULD. A subsequent comparison confirmed
that WOULD was clearer in the original. Distortion was not explicitly rated.

ASR comparison: both shifts changed WOULD to DID. Upward-shift WER was 14.29%;
downward-shift WER was 71.43%, with additional substitutions.

Some perceived difficulty locations matched model errors, but this does not
establish their cause. Listening with known text is not blind transcription and
cannot estimate human recognition accuracy. The comparison suggests reduced
clarity of WOULD after shifting in this case, without identifying an acoustic
mechanism or supporting generalization to other recordings.

The next case selected for listening was 1988-147956-0004, with the largest
upward-shift WER increase.

## 2026-09-19: 1988-147956-0004

The original was followed by the upward-shifted recording. The immediate prompt
did not display the reference, but it had already appeared in the case report;
this cannot be treated as controlled blind listening.

The listener reported greater difficulty understanding the shifted version,
with speech becoming unclear from AGAINST onward.

ASR comparison: original WER was 0%; upward-shift WER was 40.91% (22 reference
words, six substitutions, two deletions, one insertion). AGAINST itself was
recognized correctly. Errors included PRESENTLY → FINALLY, THATCHED → BASHED,
and changes near the ending THAT GREW EVERYWHERE. The reported start of an
unclear region does not imply that AGAINST was transcribed incorrectly.

Subjective difficulty and ASR errors increased together, but perceived muddiness
need not correspond to an error at every word. Neither an acoustic mechanism
nor the listening experience of the downward version was established.

The next listening case was 2277-149896-0001, which had the smallest WER change.

## 2026-09-19: 2277-149896-0001

Translated feedback: the speech after "pay her money" was somewhat unclear,
the downward shift required more effort, and understanding was unaffected after
hearing the original. This is an approximate location, not a verbatim
transcription. The reference phrase is PAY HER THE MONEY; exact boundaries of
the unclear region were not established.

Listening was arranged as original, downward, then upward. The listener explicitly
referred to hearing the original first, so the response was cued by prior content
and does not establish comprehension on first exposure to transformed audio.

ASR comparison: original and upward WER were 0%; downward WER was 3.85%, with
one DID → WOULD substitution in the later phrase IT DID NOT MATTER. That edit
cannot be directly equated with the listener's reported unclear region.

Low ASR error can coexist with subjective listening effort while familiar content
remains understandable. This is exploratory feedback from one listener, not a
quantitative measure of listening effort or intelligibility.

## Synthesis across the three cases

In the first two cases, subjective difficulty and increased ASR errors agreed
in direction, but their word locations did not always match. In the third, very
low ASR error coexisted with reported local muddiness and greater effort for the
downward shift. ASR metrics and subjective observations are therefore retained
separately; low WER is not interpreted as unchanged listening quality.

Cases were selected using metric-based rules, and listening involved reference
text or original-audio cues. These observations are limited to these cases and
this listener.
