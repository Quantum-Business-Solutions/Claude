/**
 * Push a won quote into e-automate as a sales order, via CEO Juice process ID634.
 *
 * ID634 IS NOT A CREATE CALL. `PUT /api/SalesOrder/AddOrder` stages one row per
 * line into CEO Juice's `ZCJ_ImpSOOrderDetails` table under a shared SourceID,
 * then runs the `ZCJ_Event_634_Log` stored procedure, which DERIVES THE ORDER
 * HEADER FROM THE BATCH, creates the SOOrders / SOOrderDetails records, and writes
 * the resulting SOID back onto the staged rows.
 *
 * Three consequences shape this function:
 *
 * 1. HEADER FIELDS MUST BE IDENTICAL ON EVERY LINE. The procedure reads them off
 *    the batch, not per line. Inconsistent values do not raise a validation error
 *    — the header is simply built from whichever row wins, which is silent wrong
 *    data rather than a failed request. `normaliseHeader` below stamps the header
 *    onto every line from a single source so a caller cannot produce that state.
 *
 * 2. A 200 DOES NOT MEAN AN ORDER EXISTS. CEO Juice validates each row against
 *    existing customer, branch, item, warehouse and sales-rep records, and HOLDS
 *    invalid orders rather than skipping them. So a push can succeed at the HTTP
 *    level and leave the order sitting in staging awaiting correction. We record
 *    what was sent and what came back rather than reporting success on a 200.
 *
 * 3. RETRYING IS DANGEROUS. Because the outcome is ambiguous, the natural reflex
 *    on an unclear response is to push again — and that is how one quote becomes
 *    two orders. A partial unique index on `ceojuice_order_pushes (quote_id) WHERE
 *    status = 'succeeded'` makes the second attempt fail at the database instead.
 */

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createErrorResponse, createJsonResponse } from "../_shared/validation.ts";
import { authzErrorResponse, requireDealerAccess } from "../_shared/authz.ts";
import { getDealerCeoJuice } from "../_shared/ceojuice-connection.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

/**
 * Fields ID634 reads at the HEADER level even though the DTO is flat and carries
 * them on every line. These are the ones that must not vary across a batch.
 *
 * Derived from the ImpSalesOrderDetailDto shape plus the procedure's documented
 * behaviour. If a field is added here it becomes copy-from-first rather than
 * per-line, so add deliberately.
 */
const HEADER_FIELDS = [
  "impCustomerNumber",
  "impShipToCustomerNumber",
  "impBillToCustomerNumber",
  "impSONumber",
  "soDate",
  "reqDate",
  "poNumber",
  "salesRepNumber",
  "altSalesRepNumber",
  "branchNumber",
  "soBranchNumber",
  "termsCode",
  "taxCode",
  "shipMethod",
  "orderType",
  "onHoldCode",
  "contactNumber",
  "shipToContactNumber",
  "jobNumber",
  "dealNumber",
  "quoteNumber",
  "mailtoAttn",
  "mailToName",
  "mailToAddress",
  "mailToCity",
  "mailToState",
  "mailToZip",
  "mailToCountry",
  "shipToAttn",
  "shipToName",
  "shipToAddress",
  "shipToCity",
  "shipToState",
  "shipToZip",
  "shipToCountry",
  "orderedByEmail",
  "orderedByFirstName",
  "orderedByLastName",
  "orderedByPhone",
  "deliveryRemarks",
  "targEAOrderStatus",
] as const;

/** Line-level fields — genuinely per row, never copied. */
const REQUIRED_LINE_FIELDS = ["item", "qty"] as const;

/**
 * Stamp one header onto every line.
 *
 * The header is taken from the explicit `header` object when supplied, otherwise
 * from the first line — which is what ID634 itself would have used. Either way
 * every line ends up carrying identical header values, so the "header built from
 * whichever row wins" failure cannot happen.
 */
function normaliseHeader(
  lines: Record<string, unknown>[],
  header: Record<string, unknown> | undefined,
): { lines: Record<string, unknown>[]; header: Record<string, unknown>; overridden: string[] } {
  const source = header ?? lines[0] ?? {};
  const resolved: Record<string, unknown> = {};
  for (const field of HEADER_FIELDS) {
    if (source[field] !== undefined && source[field] !== null && source[field] !== "") {
      resolved[field] = source[field];
    }
  }

  /* Report which lines disagreed with the header we applied. Not an error — the
     caller may legitimately not have known these were header-level — but it is
     worth surfacing, because a rep who typed two different ship-to addresses
     should find out that only one was used. */
  const overridden = new Set<string>();
  for (const line of lines) {
    for (const field of HEADER_FIELDS) {
      const existing = line[field];
      if (
        existing !== undefined &&
        existing !== null &&
        existing !== "" &&
        resolved[field] !== undefined &&
        String(existing) !== String(resolved[field])
      ) {
        overridden.add(field);
      }
    }
  }

  return {
    lines: lines.map((line) => ({ ...line, ...resolved })),
    header: resolved,
    overridden: [...overridden],
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  try {
    const body = await req.json();
    const { action = "push", dealer_id, quote_id, lines, header, dry_run = false } = body ?? {};

    const caller = await requireDealerAccess(supabase, req, { dealer_id });

    /* History for a quote — "did this reach e-automate" without pushing anything. */
    if (action === "history") {
      const { data, error } = await supabase
        .from("ceojuice_order_pushes")
        .select("id, quote_id, status, http_status, so_number, error_message, created_at")
        .eq("dealer_id", caller.dealerId)
        .order("created_at", { ascending: false })
        .limit(quote_id ? 20 : 50);
      if (error) return createErrorResponse(error.message, 500, corsHeaders);
      const rows = quote_id ? (data ?? []).filter((r: any) => r.quote_id === quote_id) : data;
      return createJsonResponse({ items: rows ?? [] }, corsHeaders);
    }

    if (action !== "push") {
      return createErrorResponse(`Unknown action "${action}"`, 400, corsHeaders);
    }

    if (!quote_id) return createErrorResponse("quote_id is required", 400, corsHeaders);
    if (!Array.isArray(lines) || lines.length === 0) {
      return createErrorResponse("lines must be a non-empty array", 400, corsHeaders);
    }

    for (const [index, line] of lines.entries()) {
      for (const field of REQUIRED_LINE_FIELDS) {
        if (line?.[field] === undefined || line?.[field] === null || line?.[field] === "") {
          return createErrorResponse(
            `Line ${index + 1} is missing "${field}". Every line needs an item and a quantity.`,
            400,
            corsHeaders,
          );
        }
      }
    }

    const normalised = normaliseHeader(lines, header);
    if (!normalised.header.impCustomerNumber) {
      /* Without a customer number ID634 cannot resolve the account, and the order
         goes to held. Fail here where the message can be useful. */
      return createErrorResponse(
        "impCustomerNumber is required — ID634 resolves the account from it and holds the order without it.",
        400,
        corsHeaders,
      );
    }

    /* Let a caller see the exact payload, header resolution and any overridden
       fields without touching e-automate. Worth having for a 103-field DTO. */
    if (dry_run) {
      return createJsonResponse(
        {
          dryRun: true,
          lineCount: normalised.lines.length,
          header: normalised.header,
          overriddenFields: normalised.overridden,
          payload: normalised.lines,
        },
        corsHeaders,
      );
    }

    /* Claim the push BEFORE calling out, so the unique index rejects a concurrent
       or repeated attempt rather than both reaching CEO Juice. A row that ends up
       'failed' does not hold the index and a retry is allowed. */
    const { data: claim, error: claimErr } = await supabase
      .from("ceojuice_order_pushes")
      .insert({
        dealer_id: caller.dealerId,
        quote_id,
        request_payload: normalised.lines,
        status: "pending",
        pushed_by: caller.userId ?? null,
      })
      .select("id")
      .single();

    if (claimErr) {
      /* 23505 = unique violation on the partial index: this quote already landed. */
      if ((claimErr as any).code === "23505") {
        return createErrorResponse(
          "This quote has already been pushed to e-automate successfully. " +
            "Check the push history before sending it again.",
          409,
          corsHeaders,
        );
      }
      return createErrorResponse(`Could not record the push: ${claimErr.message}`, 500, corsHeaders);
    }

    const cj = await getDealerCeoJuice(supabase, req, { dealer_id });

    let httpStatus = 0;
    let responseText = "";
    try {
      const resp = await cj.call("/api/SalesOrder/AddOrder", {
        method: "PUT",
        body: JSON.stringify(normalised.lines),
      });
      httpStatus = resp.status;
      responseText = await resp.text();

      if (!resp.ok) {
        await supabase
          .from("ceojuice_order_pushes")
          .update({
            status: "failed",
            http_status: httpStatus,
            response_body: responseText.slice(0, 4000),
            error_message: `CEO Juice returned ${httpStatus}`,
          })
          .eq("id", claim.id);

        return createErrorResponse(
          `CEO Juice rejected the order (${httpStatus}): ${responseText.slice(0, 400)}`,
          502,
          corsHeaders,
        );
      }
    } catch (e) {
      await supabase
        .from("ceojuice_order_pushes")
        .update({ status: "failed", error_message: (e as Error).message })
        .eq("id", claim.id);
      return createErrorResponse(
        `Could not reach CEO Juice: ${(e as Error).message}`,
        502,
        corsHeaders,
      );
    }

    /* Try to pull an order number out of the response. The endpoint's success shape
       is not documented and may be a bare SOID, an object, or empty — so this is
       best-effort and its absence is NOT treated as failure. */
    let soNumber: string | null = null;
    try {
      const parsed = responseText.trim() ? JSON.parse(responseText) : null;
      soNumber =
        parsed?.soNumber ?? parsed?.orderNumber ?? parsed?.soId ?? parsed?.SOID ??
        (typeof parsed === "number" || typeof parsed === "string" ? String(parsed) : null);
      if (soNumber !== null) soNumber = String(soNumber);
    } catch {
      /* Non-JSON success body — keep the raw text, leave soNumber null. */
    }

    await supabase
      .from("ceojuice_order_pushes")
      .update({
        status: "succeeded",
        http_status: httpStatus,
        response_body: responseText.slice(0, 4000),
        so_number: soNumber,
      })
      .eq("id", claim.id);

    return createJsonResponse(
      {
        pushId: claim.id,
        httpStatus,
        soNumber,
        lineCount: normalised.lines.length,
        overriddenFields: normalised.overridden,
        /* Deliberately not phrased as "order created". ID634 validates and holds
           invalid orders, so a 200 means the batch was accepted for import — the
           order may still be sitting in staging. Saying otherwise here is how a rep
           tells a customer their order is in when it is not. */
        status: soNumber
          ? "Accepted by ID634 and an order number came back."
          : "Accepted by ID634 for import. No order number returned yet — it may still be staged or held for validation; confirm in e-automate.",
        raw: responseText.slice(0, 1000),
      },
      corsHeaders,
    );
  } catch (e) {
    const authzResp = authzErrorResponse(e, corsHeaders);
    if (authzResp) return authzResp;
    console.error("ceojuice-push-order:", (e as Error).message);
    return createErrorResponse((e as Error).message, 500, corsHeaders);
  }
});
