---
name: review-roll
description: Review a BJJ sparring roll to find the positions the user lost and why. Use when the user says "review my roll", "review <clip>", or asks why they keep losing a position in a bjj-silver clip.
---

# Review a roll

Goal: find each moment the user lost a position, say what broke first, and track habits that repeat across rolls. Plain files only.

Paths (always absolute):
- PY = `C:\Users\BJJDa\bjj-roll-review\.venv\Scripts\python.exe`
- Run every helper command with `C:\Users\BJJDa\bjj-roll-review` as the working directory (`cd` there first).
- Kept files: `C:\Users\BJJDa\bjj-roll-review\reviews\`, `...\habits.md`, `...\bjj-reference.md`

## Hard rules
- Never confuse the user with their partner. If you are not sure which person is the user in a frame, say so and lower confidence. Never store anything about how the user looks.
- Only claim a "why" that the frames show. If you cannot tell (occluded, off-camera, blurry, too fast), write "can't tell from the frames". Low confidence beats a confident guess.
- Timeline positions are neutral: they do not say who is on top or who the user is. Work that out from the frames.

## Procedure

1. **Identity.** The user must say which person they are (e.g. "black rash guard, left side"). If missing, ask and stop until answered.
2. **Fetch.** Call `mcp__bjj-silver__get_clip(clip)`. Keep summary, timeline, date, portal_url. Make a fresh temp folder: `PY -c "import tempfile;print(tempfile.mkdtemp(prefix='rollreview-'))"` -> TMP. Then `PY -m rollreview get <watch_url> TMP` prints the video path. Exit 2 means the link expired: call `get_clip` again for a fresh `watch_url` and retry.
3. **Reference.** Read `bjj-reference.md` (visual cues and past corrections). Corrections override your own assumptions.
4. **First pass.** `PY -m rollreview first <video> TMP\first` prints one frame path per line (1 fps, capped at 600; a stderr note says if fps was lowered, so convert frame index to time accordingly). View the frames. Read the timeline (a position about every 20 s, skip "not visible") and mark each change as candidate moment `{t, from, to}`. Confirm the user's identity in the frames. Decide which changes went against the user: they went from better to worse (e.g. the user's guard got passed, or the user was mounted). Ignore changes in the user's favor and neutral resets.
5. **Close-ups.** For each loss: `PY -m rollreview close <video> <t_seconds> TMP\close_<t>` (8 fps over t-5 to t+1). View the frames and judge what broke first: grip, frame, posture/base, hip position, or timing. Say what you actually see. Give confidence high/medium/low. High needs the cause visible in several frames.
6. **Comparison (optional, max 3).** `mcp__bjj-silver__search_clips(position=<lost position>, type="rolling", limit=3)`. Use only their summaries and timelines, to note a repeat. Do not download them unless the user asks.
7. **Write** `C:\Users\BJJDa\bjj-roll-review\reviews\<clip>.md`:

```
# Review: <clip>
- Date: <date>
- User: <who the user said they are>
- Portal: <portal_url>

## 1. <m:ss> <from> -> <to>
- What happened: ...
- Why: ... (or "can't tell from the frames")
- Confidence: high | medium | low
```
One section per lost battle, numbered. If there are no clear losses, say so in the file.
8. **Habits.** Update `habits.md`, a table with columns `habit | count | clips | latest example`. If an existing row has the same lost position and the same cause, add 1 to count, append the clip, and replace the latest example. Otherwise add a row. Do not count low-confidence "can't tell" losses as a cause.
9. **Clean up.** Delete the whole TMP folder (`rm -rf` / `Remove-Item -Recurse -Force`), even if you stopped early or hit an error.
10. **Corrections.** When the user corrects a term or call ("that was a lasso, not spider"), append it under "Corrections" in `bjj-reference.md`.

Finish with a short summary: losses found, top cause, review file path.
