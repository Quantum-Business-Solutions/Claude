// Unipile read-only relay.
//
// Why this exists: Unipile serves its tenant API on port 16072. Anthropic cloud
// sessions can only make outbound connections on port 443, so Python in a routine
// cannot reach Unipile at all. The MCP connector worked around that by tunnelling
// through Anthropic's proxy, but routine-fired sessions get no connector tools, so
// every scheduled run had no path to LinkedIn and silently did nothing.
//
// This relay sits on 443 and forwards to 16072. With it, the verification scripts
// reach Unipile over ordinary HTTPS from anywhere - an interactive session, a
// Routine, a Cowork task, cron - and the connector stops mattering.
//
// It deliberately holds NO credential. The caller passes its own X-API-KEY, which is
// forwarded unchanged. Without a valid Unipile key this endpoint can do nothing.
//
// Safety properties, all enforced below:
//   - GET/HEAD only, so it can read profiles and can never send an invite, DM or InMail
//   - target host is hardcoded, so it cannot be used as an open proxy
//   - account_id, when present, must be one of Shawn's two accounts; the five client
//     identities on the same tenant are rejected here, not merely by convention
//   - Supabase JWT verification is on, so an Authorization bearer is required as well

import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const UPSTREAM = "https://api30.unipile.com:16072";

// Shawn's own LinkedIn accounts. Every other account on this tenant belongs to a
// client and must never be used by this process.
const ALLOWED_ACCOUNTS = new Set([
  "S6ua4SfUT4SMRFZFOmyUzQ",
  "7lBoyXuETqKdiJYLj5HBGA",
]);

const TIMEOUT_MS = 25_000;

function deny(status: number, error: string, detail?: string): Response {
  return new Response(JSON.stringify({ relay_error: error, detail }), {
    status,
    headers: { "content-type": "application/json" },
  });
}

Deno.serve(async (req: Request) => {
  if (req.method !== "GET" && req.method !== "HEAD") {
    return deny(
      405,
      "read_only",
      "This relay forwards GET only. It cannot perform LinkedIn actions.",
    );
  }

  const url = new URL(req.url);

  // Supabase routes /functions/v1/<name>/<rest> here; strip both prefixes.
  let rest = url.pathname
    .replace(/^\/functions\/v1/, "")
    .replace(/^\/unipile-relay/, "");
  if (rest === "" || rest === "/") {
    return new Response(
      JSON.stringify({
        relay: "unipile-read-only",
        upstream: UPSTREAM,
        methods: ["GET", "HEAD"],
        usage: "GET /unipile-relay/users/<identifier>?account_id=...&linkedin_sections=experience",
        note: "Send your own X-API-KEY. This relay stores no credential.",
      }),
      { headers: { "content-type": "application/json" } },
    );
  }
  if (!rest.startsWith("/api/")) rest = "/api/v1" + rest;

  const accountId = url.searchParams.get("account_id");
  if (accountId !== null && !ALLOWED_ACCOUNTS.has(accountId)) {
    return deny(
      403,
      "account_not_allowed",
      "Only Shawn's own Unipile accounts may be used. Client identities share this tenant and are blocked here.",
    );
  }

  const apiKey = req.headers.get("x-api-key");
  if (!apiKey) {
    return deny(
      400,
      "missing_api_key",
      "Supply the Unipile key as X-API-KEY. This relay holds none of its own.",
    );
  }

  const target = UPSTREAM + rest + url.search;
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers: { "X-API-KEY": apiKey, accept: "application/json" },
      signal: ctl.signal,
    });
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: {
        "content-type": upstream.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (e) {
    const aborted = e instanceof Error && e.name === "AbortError";
    return deny(
      aborted ? 504 : 502,
      aborted ? "upstream_timeout" : "upstream_unreachable",
      String(e),
    );
  } finally {
    clearTimeout(timer);
  }
});
