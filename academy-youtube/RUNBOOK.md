# Quantum Academy → YouTube, one batch a day

Shawn asked (2026-09-28) for every Quantum Academy video to go up on the
YouTube channel (The.Shawn.Peterson, `UCLLt7UtBjyeiOiUAYHd6C-Q`), public, a
batch each day until the Academy is fully uploaded.

## How the upload actually happens

ClientCommand (Supabase project `zjtgesaiemlveuoymubo`) already has the
machinery; nothing here uploads bytes itself.

- Table `youtube_uploads`: one row per video. Insert a row with
  `status = 'pending'` and the cron does the rest.
- Cron `youtube-upload-continue` runs every 3 minutes and calls the
  `youtube-upload` edge function with `continue_pending`. That opens the
  YouTube resumable session and streams the file from `source_ref` in
  8 MiB ranged chunks. `source_ref` must answer HTTP Range requests with
  206. HubSpot file URLs and the Supabase academy bucket both do.
- The channel has a daily **Video Uploads** quota. On 2026-09-25, about 14
  uploads succeeded and the rest got `429 Quota exceeded`. A row that hits
  429 retries on each tick and is marked `failed` after 12 attempts (about
  36 minutes). So queue at most **9 a day** (see step 1). Other tools also upload to
  this channel, BrandCommand among them, and they share the quota.
- Reading or editing a live video (title, description, privacy) goes
  through the ClientCommand MCP `call_internal_api`, with
  `service = "youtube_oauth"` and a path starting `/youtube/v3/...`.
  Example: `PUT /youtube/v3/videos?part=snippet,status`.

## Files

- `manifest_week1.json` holds the 15 Revenue Efficiency Model chapters
  (Week One of the Sales Bootcamp), fully titled. Chapters 1–10 were
  queued on 2026-09-28.
- `manifest_rest.json` has three lists:
  - `queue` is everything else, in upload order. Most entries have
    `title: null`, so write the title from the content (see below).
  - `hold` is **not to upload without Shawn's OK**: the ConnectAndSell
    vendor training and the Welcome to Quantum onboarding course.
  - `skipped` is already on YouTube.
- `batch1.sql` is the insert pattern: `jsonb_to_recordset`, with `tags` as
  jsonb converted to `text[]`, and a `not exists` guard on `source_ref` so
  a re-run never double-queues.

## Daily run

0. **Setup, if the container is fresh.** The local branch can come back
   rebuilt from `main` without these files. If it does, run
   `git fetch origin claude/linkedin-engagement-task-debug-5o6xu1` and
   then `git checkout -B claude/linkedin-engagement-task-debug-5o6xu1 origin/claude/linkedin-engagement-task-debug-5o6xu1`,
   after checking that the local branch has no commits of its own. Then
   `pip install faster-whisper av`.

   Titles from the chapter name are wrong even inside Quantum Sales
   Training. `QBS_1`, `QBS_2` and `QBS_3` there are the Go-to-Market
   Playbook intro and the Quantum Growth Model, not goal-setting lessons.
   Transcribe every file.

1. **Check yesterday.** List every row queued by this job:

   ```sql
   select id, status, left(title,70) t, youtube_video_id, attempts, left(coalesce(error,''),120) e
   from youtube_uploads
   where context->>'queued_by' = 'claude-daily-academy-upload'
   order by created_at;
   ```

   Rows that failed on quota with no `youtube_upload_url` are safe to
   requeue. Quota shows up as either `429` or `400 uploadLimitExceeded`
   ("The user has exceeded the number of videos they may upload"). The
   10th upload of the day hit the 400 version on both 2026-09-30 and
   2026-10-01, so queue **9 a day** (requeues included). To requeue, set
   `status='pending', attempts=0, error=null` and count the row toward
   today's 9. Rows that failed for any other reason need a
   diagnosis first. Don't blindly retry them.
2. **Verify completions.** For each completed row, check
   `GET /youtube/v3/videos?part=status,snippet&id=...`. It should be
   public, embeddable, and have the right title. Fix anything off with a
   PUT.
3. **Pick today's batch.** The cap is 9 rows (new or requeued) in the
   last 20 hours. If that many already exist, queue nothing new and only do
   steps 1–2. Finish `manifest_week1.json` first, then take
   `manifest_rest.json` → `queue` in `priority` order.
4. **Title from content, never from the Academy chapter name.** The
   Academy has files attached to the wrong chapters and courses. The
   "Attitude" course, for example, holds Patrick Metzger webinar
   chapters. For each file:
   - Download it with `curl -A "Mozilla/5.0"`. Plain urllib gets a 403
     from HubSpot.
   - Get the duration with PyAV.
   - Transcribe with faster-whisper `small.en`, int8: the first ~75 s, a
     middle slice, and the last ~45 s.
   - Write the title: specific and search-shaped, at most 70 characters,
     no clickbait, no em dashes.
   - Write a 2–3 sentence description of what the viewer learns, a series
     line if the video is part of a course, and the footer used in
     `manifest_week1.json`: a relevant page on thequantumleap.business
     with UTM tags, the meeting link, and Shawn's bio line.
   - `title_hint` / `summary_hint` in `manifest_rest.json` came from an
     earlier transcript of a different export of the same lesson. Use
     them only if the opening transcript confirms the topic. Use
     `hint_chapters` timestamps only if the duration is within 2 s of
     `hint_duration_s`.
   - Watch for shorter cuts. Several lessons exist as a full file plus
     `_A`/`_B` or `_1`/`_2` halves (QBS_6 = 6_A + 6_B, QBS_8 = 8_1 + 8_2).
     If the durations add up and the openings match, upload only the
     full file and move the cuts to `skipped` with a `skip_reason`.
   - Guest webinars (Metzger, Grice, the ZoomInfo webinar with Ben
     Salzman): name the guest in the title or description.
   - Anything that turns out to be client-specific, confidential, or
     another company's material goes to `hold` with a reason, not the
     queue.
5. **Insert** with the `batch1.sql` pattern: `privacy_status='public'`,
   `category_id='27'`, `context.queued_by='claude-daily-academy-upload'`.
   Mark each entry in the manifest `queued` with its `youtube_uploads.id`.
   Commit and push the manifest.
6. **Report in two or three lines:** what went live since yesterday, what
   is queued today, how many are left, and anything put on hold.

When `queue` is empty and every row is completed, say so, list whatever is
still on `hold` for Shawn to decide, and delete the daily routine.
