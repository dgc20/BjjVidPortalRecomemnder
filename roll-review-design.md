# Roll Review: short design

## Why
You want to find your bad habits: the key positional battles you lose, and why you lose them. Watching a roll yourself shows *what* happened. This is meant to show *why*, and which losses repeat across many rolls.

## Goals
- Review one roll on request and find each moment where you lost a position.
- For each loss, explain what broke first: the grip, the frame, your posture, the timing.
- Keep a running habits log that counts the losses that repeat across rolls.

## Non-goals
- A play-by-play of everything that happened.
- Breakdowns of other people's competition matches.
- Training a separate model.

## Anti-goals
These would make it a failure even if it technically works:
- Confident "why" explanations I can't actually see in the frames. Where I can't tell, the review says so.
- Mixing you up with your partner.

## Approaches considered
- **A. A review command plus a running habits log, all plain files.** This is the one you picked.
- B. A plus a visual tracker page. Set aside for now; it can be added once the habits log proves useful.
- C. Automatic body tracking. Rejected, because it fails when two people are tangled together.

## How it works
1. **You ask.** For example: "review IMG_1532, I'm in the black rash guard." You tell me which person you are every time. Nothing about how you look is stored.
2. **Fetch.** I look up the clip in bjj-silver with `get_clip` or `search_clips` and download it from its `watch_url`. I also take its summary and position timeline.
3. **First pass.** I pull 1 frame per second and use the timeline as a rough guide to find each position change that went against you.
4. **Close-up pass.** For each of those moments, I pull 8–10 frames per second from the 5 seconds before it and work out what broke first.
5. **Comparison.** I search bjj-silver for other clips with the same position and check whether the loss looks the same.
6. **Write-up.**
   - `reviews/<clip>.md`: each lost battle with its timestamp, what happened, why, my confidence (high/medium/low), and the clip link.
   - `habits.md`: one row per repeating habit, with a count, the clips it shows up in, and the latest example.
   - `bjj-reference.md`: your terms and corrections. I read it before every review, and when you correct me ("that was a lasso, not spider"), the correction goes here.
7. **Packaged as a skill** (`review-roll`), so "review my roll" works in any future session.

## Constraints
- The clip links expire after a few hours, so I download a fresh one on every review.
- Frames are deleted after each review. Only the write-ups are kept.
- Rolls of about 5–10 minutes work best. Longer clips cost more.
- ffmpeg must be installed. I'll check for it and install it if needed.

## Where files go
In a folder you choose. Right now this doc sits in a folder the app made for this session, which is deleted along with the session.

## Left to the builder
The exact frame rates and window sizes, file formatting, and how habits get grouped (same position, similar cause).
