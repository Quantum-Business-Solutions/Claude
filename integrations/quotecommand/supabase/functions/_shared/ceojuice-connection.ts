/**
 * Dealer-scoped CEO Juice access. Every CEO Juice edge function goes through this.
 *
 * Deliberately shaped like `hubspot-connection.ts` — same authorize-then-look-up
 * order, same `callJson` surface — so the two integrations read the same way.
 * What differs is authentication, and it differs in one way that matters:
 *
 *   HubSpot   → OAuth. We hold a refresh token; the credential is never ours.
 *   CEO Juice → username + password traded for a six-hour JWT. There is NO
 *               refresh grant, so the credential itself has to persist and the
 *               only way to renew is to log in again.
 *
 * WHY THE TOKEN IS CACHED IN THE ROW, not in a module variable. Edge functions
 * are stateless and a module-level cache survives only as long as one warm
 * isolate, so a burst of invocations would each perform their own login. The dev
 * host resets connections under sustained sequential load, which makes redundant
 * logins actively harmful rather than merely wasteful. The JWT and its expiry
 * live on `ceojuice_dealer_connections` and are reused until they are nearly
 * spent.
 *
 * WHY THE SKEW IS A FULL MINUTE. A token that expires mid-invocation produces a
 * 401 from a call that looked fine when it was issued, and the retry path cannot
 * distinguish that from a revoked credential. Refreshing a minute early costs one
 * extra login every six hours and removes the class of bug.
 *
 * WHAT THIS HELPER DOES NOT DO: it does not send the `eaapikey` header. The
 * Swagger document declares `ApiKey` and `Bearer` in a single security
 * requirement block, which reads as though both are mandatory. They are not —
 * verified against the live API, Bearer alone returns 200 and the JWT already
 * carries `ApiKeyId`. Sending a bogus `eaapikey` alongside it is what you would
 * do from reading the spec, and it is unnecessary.
 */

import { decryptSecret, encryptSecret } from "./crypto.ts";
import { requireDealerAccess } from "./authz.ts";

/** Refresh this far before the stated expiry — see note above. */
const EXPIRY_SKEW_MS = 60_000;

/**
 * Lookup lists live under two families in the API. The `/api/ListsAndCodes/*`
 * family is gated on a claim that ordinary dealer keys do not carry and answers
 * 403 for all nineteen routes; every list is duplicated under a domain-scoped
 * route gated on the domain claim instead, and those answer. Callers ask for a
 * list by name and get the route that works.
 */
export const CEOJUICE_LIST_ROUTES: Record<string, string> = {
  CallTypes: "/api/ServiceCall/CallTypes",
  ProblemCodes: "/api/ServiceCall/ProblemCodes",
  RepairCodes: "/api/ServiceCall/RepairCodes",
  CancelCodes: "/api/ServiceCall/CancelCodes",
  OnHoldCodes: "/api/ServiceCall/OnHoldCodes",
  Priorities: "/api/ServiceCall/Priorities",
  NoteTypes: "/api/ServiceCall/NoteTypes",
  SLACodes: "/api/ServiceCall/SLACodes",
  States: "/api/Customer/States",
  Countries: "/api/Customer/Countries",
  Terms: "/api/Customer/Terms",
  PriceLevels: "/api/Customer/PriceLevels",
  OrderTypes: "/api/SalesOrder/OrderTypes",
  OrderStatuses: "/api/SalesOrder/OrderStatuses",
  ShipMethods: "/api/SalesOrder/ShipMethods",
  MeterTypes: "/api/MeterReadings/MeterTypes",
  Makes: "/api/Item/Makes",
  Models: "/api/Item/Models",
  ModelCategories: "/api/Item/ModelCategories",
};

export interface DealerCeoJuice {
  dealerId: string;
  baseUrl: string;
  /** From the JWT's own claims — which e-automate tenant this credential reaches. */
  customerNumber: string;
  customerName: string;
  apiKeyId: string;
  call: (path: string, init?: RequestInit) => Promise<Response>;
  callJson: <T = unknown>(path: string, init?: RequestInit) => Promise<T>;
  /** Walk a paged endpoint and collect every item. */
  paginate: <T = unknown>(path: string, pageSize?: number, maxPages?: number) => Promise<T[]>;
  getList: (name: string) => Promise<unknown[]>;
}

interface ConnectionRow {
  dealer_id: string;
  base_url: string;
  username: string;
  password_encrypted: string;
  access_token: string | null;
  token_expires_at: string | null;
  api_key_id: string | null;
  customer_number: string | null;
  customer_name: string | null;
}

/** Claims we lift off the JWT so the UI can show what a credential actually reaches. */
interface TokenIdentity {
  apiKeyId: string;
  customerNumber: string;
  customerName: string;
}

/**
 * Decode a JWT payload without verifying it.
 *
 * Verification would need CEO Juice's signing secret, which we do not have and
 * should not — the token is not a credential we are validating, it is one we were
 * just handed over TLS by the issuer. We read it only to display which tenant the
 * dealer is bound to, so a malformed token degrades to empty strings rather than
 * throwing and taking the login down with it.
 */
function readTokenIdentity(token: string): TokenIdentity {
  try {
    const payload = token.split(".")[1];
    if (!payload) return { apiKeyId: "", customerNumber: "", customerName: "" };
    const normalised = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalised + "=".repeat((4 - (normalised.length % 4)) % 4);
    const claims = JSON.parse(atob(padded));
    return {
      apiKeyId: String(claims.ApiKeyId ?? ""),
      customerNumber: String(claims.CustomerNumber ?? ""),
      customerName: String(claims.CustomerName ?? ""),
    };
  } catch {
    return { apiKeyId: "", customerNumber: "", customerName: "" };
  }
}

/** POST /api/Auth/token. Returns the JWT plus the identity encoded in it. */
export async function ceoJuiceLogin(
  baseUrl: string,
  username: string,
  password: string,
): Promise<{ token: string; expiresAt: string; identity: TokenIdentity }> {
  const resp = await fetch(`${baseUrl.replace(/\/+$/, "")}/api/Auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const text = await resp.text();
  if (!resp.ok) {
    /* 401 here means the credential is wrong, which is a different problem for the
       dealer than the host being down — say which. */
    if (resp.status === 401) {
      throw new Error("CEO Juice rejected the username or password.");
    }
    throw new Error(`CEO Juice login failed → ${resp.status}: ${text.slice(0, 300)}`);
  }
  const data = JSON.parse(text) as { token: string; expires: string };
  if (!data?.token) throw new Error("CEO Juice login returned no token.");
  return {
    token: data.token,
    expiresAt: new Date(data.expires).toISOString(),
    identity: readTokenIdentity(data.token),
  };
}

/**
 * Percent-encode a value used as a URL path segment.
 *
 * Not defensive boilerplate — e-automate equipment numbers genuinely contain
 * spaces ("EQ100023 Dept 330"), and interpolating one raw produces a request that
 * fails before it is sent. Every path built from dealer data goes through this.
 */
export function seg(value: string | number): string {
  return encodeURIComponent(String(value));
}

export async function getDealerCeoJuice(
  supabase: any,
  /* REQUIRED, and second, matching getDealerHubSpot so that authorization is
     structurally impossible to omit. `qa/edge-authz.ts` enforces this shape. */
  req: Request,
  params: { dealer_id?: string | null },
): Promise<DealerCeoJuice> {
  if (!req || typeof (req as Request).headers?.get !== "function") {
    throw new Error(
      "getDealerCeoJuice requires the incoming Request so the caller can be authorized. " +
        "Pass `req` as the second argument.",
    );
  }

  /* Throws AuthzError (401/403/404). The VERIFIED dealer id is what we look the
     connection up by — checking one value then querying by another is the bug
     class this ordering exists to prevent. */
  const caller = await requireDealerAccess(supabase, req, params);

  const { data, error } = await supabase
    .from("ceojuice_dealer_connections")
    .select(
      "dealer_id, base_url, username, password_encrypted, access_token, token_expires_at, api_key_id, customer_number, customer_name",
    )
    .eq("dealer_id", caller.dealerId)
    .maybeSingle();

  if (error) throw new Error(`CEO Juice connection lookup failed: ${error.message}`);
  if (!data) {
    throw new Error(
      `No CEO Juice connection for dealer ${caller.dealerId} — add one in Settings → Integrations.`,
    );
  }

  const row = data as ConnectionRow;
  const baseUrl = row.base_url.replace(/\/+$/, "");

  let token = row.access_token ?? "";
  let identity: TokenIdentity = {
    apiKeyId: row.api_key_id ?? "",
    customerNumber: row.customer_number ?? "",
    customerName: row.customer_name ?? "",
  };

  const expiresAtMs = row.token_expires_at ? Date.parse(row.token_expires_at) : 0;
  const stale = !token || !expiresAtMs || Date.now() >= expiresAtMs - EXPIRY_SKEW_MS;

  if (stale) {
    const password = await decryptSecret(row.password_encrypted, "CEOJUICE_CREDENTIAL_ENCRYPTION_KEY");
    try {
      const fresh = await ceoJuiceLogin(baseUrl, row.username, password);
      token = fresh.token;
      identity = fresh.identity;
      await supabase
        .from("ceojuice_dealer_connections")
        .update({
          access_token: fresh.token,
          token_expires_at: fresh.expiresAt,
          api_key_id: fresh.identity.apiKeyId,
          customer_number: fresh.identity.customerNumber,
          customer_name: fresh.identity.customerName,
          last_connected_at: new Date().toISOString(),
          last_error: null,
        })
        .eq("dealer_id", caller.dealerId);
    } catch (e) {
      /* Record why, so Settings can show "the password changed" without a live
         call, then rethrow — the caller still has no usable token. */
      await supabase
        .from("ceojuice_dealer_connections")
        .update({ last_error: (e as Error).message })
        .eq("dealer_id", caller.dealerId);
      throw e;
    }
  }

  const call = async (path: string, init: RequestInit = {}): Promise<Response> => {
    const url = path.startsWith("http")
      ? path
      : `${baseUrl}${path.startsWith("/") ? "" : "/"}${path}`;
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${token}`);
    headers.set("Accept", "application/json");
    if (typeof init.body === "string" && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    /* The host resets connections under sustained sequential load and a bulk pull
       walks many pages, so transient faults are expected rather than
       exceptional. 429 and 5xx retry on the same path; 4xx is a real answer about
       the request and returns immediately. */
    let lastErr: unknown;
    for (let attempt = 0; attempt <= 3; attempt++) {
      try {
        const resp = await fetch(url, { ...init, headers });
        if (resp.status === 429 || resp.status >= 500) {
          if (attempt === 3) return resp;
          await new Promise((r) => setTimeout(r, 2 ** attempt * 500));
          continue;
        }
        return resp;
      } catch (e) {
        lastErr = e;
        if (attempt === 3) break;
        await new Promise((r) => setTimeout(r, 2 ** attempt * 500));
      }
    }
    throw new Error(`CEO Juice request failed: ${(lastErr as Error)?.message ?? "network error"}`);
  };

  const callJson = async <T = unknown>(path: string, init: RequestInit = {}): Promise<T> => {
    const resp = await call(path, init);
    const text = await resp.text();
    if (!resp.ok) {
      throw new Error(
        `CEO Juice ${init.method || "GET"} ${path} → ${resp.status}: ${text.slice(0, 400)}`,
      );
    }
    if (!text.trim()) return null as T;
    try {
      return JSON.parse(text) as T;
    } catch {
      return text as unknown as T;
    }
  };

  const paginate = async <T = unknown>(
    path: string,
    pageSize = 100,
    maxPages = 50,
  ): Promise<T[]> => {
    const out: T[] = [];
    for (let page = 1; page <= maxPages; page++) {
      const joiner = path.includes("?") ? "&" : "?";
      const payload = await callJson<any>(`${path}${joiner}page=${page}&pageSize=${pageSize}`);
      /* Most collections answer {page,pageSize,totalCount,totalPages,items}, but a
         handful ignore paging and return a bare array — treat that as one page. */
      if (Array.isArray(payload)) return payload as T[];
      if (!payload?.items) break;
      out.push(...(payload.items as T[]));
      if (page >= (payload.totalPages ?? 0)) break;
    }
    return out;
  };

  const getList = async (name: string): Promise<unknown[]> => {
    const route = CEOJUICE_LIST_ROUTES[name];
    if (!route) {
      throw new Error(
        `Unknown CEO Juice list "${name}". Known: ${Object.keys(CEOJUICE_LIST_ROUTES).join(", ")}`,
      );
    }
    const rows = await callJson<unknown>(route);
    return Array.isArray(rows) ? rows : [];
  };

  return {
    dealerId: caller.dealerId,
    baseUrl,
    customerNumber: identity.customerNumber,
    customerName: identity.customerName,
    apiKeyId: identity.apiKeyId,
    call,
    callJson,
    paginate,
    getList,
  };
}

/** Re-exported so `ceojuice-connection-save` encrypts with the same key name. */
export { encryptSecret };
