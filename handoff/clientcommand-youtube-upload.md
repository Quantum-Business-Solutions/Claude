# Task for a Claude Code session on Quantum-Business-Solutions/clientcommand

Add a Client Command MCP tool, `youtube_upload_from_url`, so Claude can publish a video to the connected YouTube channel in one call, given a public video URL.

## Why it fails today

The `youtube_oauth` service (OAuth as the owner of @the.shawn.peterson, channel UCLLt7UtBjyeiOiUAYHd6C-Q) works, but `call_internal_api` only sends JSON and returns only the body.

YouTube's resumable upload works in three steps:
1. POST `/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status` with the metadata.
2. The session URI comes back in the `Location` response header (the body is empty).
3. The raw bytes are PUT to that URI.

Step 1 worked (status 200, body ""). The header was dropped, and there's no way to send the bytes.

## What to build

**Inputs:**
- Required: `source_url`, `title`, `description`, `reason`.
- Optional:
  - `tags[]`
  - `privacy_status` (public | unlisted | private; default private)
  - `category_id` (default "28")
  - `made_for_kids` (default false)
  - `thumbnail_url`
  - `playlist_id`
  - `publish_at` (requires private)
  - `notify_subscribers` (default true)

**Steps:**
1. Load and refresh the `youtube_oauth` token server-side, the same way `call_internal_api` does. Never return it.
2. HEAD `source_url` for Content-Length and Content-Type. It must be https and `video/*`, and 2 GB or less. Reject private IPs to prevent SSRF. The hosts `d3snorpfx4xhv8.cloudfront.net` and `*.hubspotusercontent-na1.net` must work.
3. Send the resumable init with the headers `X-Upload-Content-Length` and `X-Upload-Content-Type`.
   - Body: `{snippet:{title,description,tags,categoryId,defaultLanguage:"en",defaultAudioLanguage:"en"},status:{privacyStatus,selfDeclaredMadeForKids,embeddable:true,publicStatsViewable:true,publishAt?}}`.
   - Read the `Location` header.
4. Stream the source body into a PUT to that Location, without buffering the whole file.
   - If the function's time limit is too short, upload in chunks that are multiples of 8 MB, using `Content-Range` and resuming on 308.
   - Or run it as a background job (`EdgeRuntime.waitUntil` plus a status row) and add a `youtube_upload_status` tool.
5. After upload:
   - If `thumbnail_url` is set: POST `/upload/youtube/v3/thumbnails/set?videoId=` with the raw bytes (jpeg/png, 2 MB or less).
   - If `playlist_id` is set: insert a playlistItem.
6. Log to `credential_access_log`. Surface `quotaExceeded` and `uploadLimitExceeded` errors clearly.
7. Return `{video_id, url:"https://youtu.be/<id>", privacy_status, thumbnail_set, processing_status}`.
8. Update the `youtube_oauth` row's notes to mention the new tool.

## First real run (already approved by Shawn: PUBLIC)

- source_url: https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/a1c05764-f908-41c6-a2c0-4f53eced0d5f.mp4
- thumbnail_url: https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/QUANTUM/VIDEOS/old-way-vs-quantum-way/old-way-vs-quantum-way-poster.jpg
- title, description and tags: copy them exactly from `video/old-way-vs-quantum-way/youtube.md` in Quantum-Business-Solutions/Claude.
- category_id 28, privacy public, made_for_kids false.
- Before retrying, check the channel for an existing video with the same title, so it's uploaded only once.

**Done means:** the tool is merged and deployed, and the video is live and public with its thumbnail, with the youtu.be link reported back.
