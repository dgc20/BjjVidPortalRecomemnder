---
name: review-roll
description: Review a BJJ sparring roll to find the positions the user lost and why. Use when the user says "review my roll", "review <clip>", or asks why they keep losing a position in a bjj-silver clip.
---

# Review a roll

Goal: find each moment the user lost a position, say what broke first, and track habits that repeat across rolls. Plain files only.

## Setup
Run all commands in the **PowerShell tool**, always quoting paths. Helper CLI (run with the repo as working directory):
```
Set-Location "C:\Users\BJJDa\bjj-roll-review"
$py = "C:\Users\BJJDa\bjj-roll-review\.venv\Scripts\python.exe"
& $py -m rollreview get "<watch_url>" "$tmp"            # prints video path
& $py -m rollreview first "$video" "$tmp\first"         # 1 fps frames, one path per line
& $py -m rollreview close "$video" 83.5 "$tmp\close_83" # 8 fps over [t-5, t+1]
```
The helper creates the output folders itself. Make `$tmp` first: `$tmp = (New-Item -ItemType Directory -Path (Join-Path $env:TEMP "rollreview-$(Get-Date -Format yyyyMMddHHmmss)")).FullName`.
Kept files: `C:\Users\BJJDa\bjj-roll-review\reviews\`, `...\habits.md`, `...\bjj-reference.md`.

## Hard rules
- Never confuse the user with their partner. If unsure who is who in a frame, say so and lower confidence.
- Use the user's "which one are you" answer only during this review. Never write it, or anything about how anyone looks, to any file. In the review text say "you" and "your partner".
- Only claim a "why" the frames show. If you can't tell (occluded, off-camera, blurry, too fast), write "can't tell from the frames". Low confidence beats a confident guess.
- Timeline positions are neutral (no top/bottom, no user). bjj-silver tags describe "the pair nearest the camera", which may not be the user's pair. If the user isn't in that pair, trust the frames, not the tags.

## What counts as a loss
Any change that leaves the user worse off: swept from top, guard passed (to side control/mount), back or mount given up, taken down, or an advantageous leg entanglement lost. A neutral reset (scramble -> standing) is not a loss. If the frames can't show who ended up on top, mark it low confidence or ask the user. Don't guess.

## Procedure
1. **Identity.** The user must say which person they are. If missing, ask and stop until answered.
2. **Fetch.** `mcp__bjj-silver__get_clip(clip)`; keep summary, timeline, date, portal_url. Create `$tmp`, then run `get`. Exit 2 means the link expired: call `get_clip` again for a fresh `watch_url` and retry.
3. **Reference.** Read `bjj-reference.md`. Its Corrections override your assumptions.
4. **First pass.** Run `first` (capped at 600 frames; a stderr note means fps was lowered, so convert frame index to time). Don't view all frames. Read the timeline (about one entry per 20 s, skip "not visible"), and view a few frames from ~10 s before to ~5 s after each position change, plus a sparse skim (about one frame per 10 s) to catch changes the coarse timeline missed. Confirm who the user is. Refine each candidate to the actual second the change happened, then decide which are losses.
5. **Close-ups.** For each loss, run `close` with the refined t (the window is only t-5 to t+1, so a coarse t can miss it; if the change isn't in view, rerun with a corrected t). Judge what broke first: grip, frame, posture/base, hips, or timing. Rate confidence high/medium/low; high needs the cause visible in several frames.
6. **Comparison (optional, max 3).** `mcp__bjj-silver__search_clips(position=<lost position>, type="rolling", limit=3)`. Use only summaries and timelines to note repeats. Don't download them unless asked.
7. **Write** `C:\Users\BJJDa\bjj-roll-review\reviews\<clip>.md`:
```
# Review: <clip>
- Date: <date>
- Portal: <portal_url>

## 1. <m:ss> <from> -> <to>
- What happened: ...
- Why: ... (or "can't tell from the frames")
- Confidence: high | medium | low
```
One numbered section per lost battle. If none, say so.
8. **Habits.** Update `habits.md` (table `habit | count | clips | latest example`). If a row has the same lost position and cause, add 1 to count, append the clip, replace the latest example; else add a row. Don't count "can't tell" losses as a cause.
9. **Clean up, even if you stopped early:** `Remove-Item -Recurse -Force "$tmp"`.
10. **Corrections.** When the user corrects a term or call, append it under "Corrections" in `bjj-reference.md`.

Finish with a short summary: losses found, top cause, review file path.
