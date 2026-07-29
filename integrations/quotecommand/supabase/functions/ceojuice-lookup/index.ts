/**
 * Read side of the CEO Juice connection — the e-automate data a quote is built from.
 *
 * Customers, equipment (with its meters and average volumes), contracts and the
 * lookup lists a sales order needs to reference. One function with an `action`
 * rather than nine functions, matching `hubspot-get-equipment` and its siblings.
 *
 * WHY LOOKUPS ARE FETCHED BY NAME. The `/api/ListsAndCodes/*` family answers 403
 * for an ordinary dealer key — all nineteen routes — while the same nineteen lists
 * are served under domain-scoped routes that do answer. Callers pass
 * `list: "OrderTypes"` and `getList` resolves the route that works, so a caller
 * cannot accidentally reach for the family that 403s.
 */

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createErrorResponse, createJsonResponse } from "../_shared/validation.ts";
import { authzErrorResponse } from "../_shared/authz.ts";
import { getDealerCeoJuice, seg } from "../_shared/ceojuice-connection.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

/**
 * A machine plus the meters and average volumes attached to it.
 *
 * WHY THE AVERAGES ARE REPORTED AS possiblyUnpopulated. e-automate computes
 * avgMonthlyVolume3Mo/6Mo/12Mo/Install itself, so where reading history exists
 * these are authoritative and need no arithmetic. Where it does not, they are
 * 0.0 — and 0.0 is indistinguishable from a machine that genuinely printed
 * nothing. Against the CEO Juice sandbox every one of 34 meters reads 0.0.
 *
 * That distinction has to reach the UI, because a quote sized from a fleet's
 * volume is wrong in an expensive direction if the volume was actually "unknown"
 * rendered as zero. There is also no meter-reading history route on this API, so
 * a zero cannot be recomputed from the raw series — it is not exposed. Hence the
 * flag rather than a silent number.
 */
function summariseMeters(meters: any[]): {
  meters: any[];
  totalAvgMonthly: number;
  possiblyUnpopulated: boolean;
} {
  const rows = Array.isArray(meters) ? meters : [];
  const total = rows.reduce(
    (sum, m) => sum + (Number(m?.avgMonthlyVolume12Mo) || Number(m?.avgMonthlyVolume3Mo) || 0),
    0,
  );
  return {
    meters: rows,
    totalAvgMonthly: total,
    possiblyUnpopulated: rows.length > 0 && total === 0,
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
    const { action, dealer_id } = body ?? {};
    if (!action) return createErrorResponse("Missing action", 400, corsHeaders);

    /* Authorizes the caller against the dealer, then resolves (and refreshes) the
       dealer's CEO Juice token. */
    const cj = await getDealerCeoJuice(supabase, req, { dealer_id });

    switch (action) {
      /* Which e-automate tenant this credential reaches, straight off the JWT
         claims. Cheap enough to call on a settings page render. */
      case "whoami":
        return createJsonResponse(
          {
            baseUrl: cj.baseUrl,
            apiKeyId: cj.apiKeyId,
            customerNumber: cj.customerNumber,
            customerName: cj.customerName,
            claims: await cj.callJson("/api/Test"),
          },
          corsHeaders,
        );

      case "customers": {
        const { page = 1, pageSize = 100, all = false } = body;
        if (all) {
          return createJsonResponse({ items: await cj.paginate("/api/Customer", 100) }, corsHeaders);
        }
        return createJsonResponse(
          await cj.callJson(`/api/Customer?page=${Number(page)}&pageSize=${Number(pageSize)}`),
          corsHeaders,
        );
      }

      case "customer": {
        const { customer_number } = body;
        if (!customer_number) {
          return createErrorResponse("customer_number is required", 400, corsHeaders);
        }
        return createJsonResponse(
          await cj.callJson(`/api/Customer/${seg(customer_number)}`),
          corsHeaders,
        );
      }

      case "contacts": {
        const { customer_number } = body;
        if (!customer_number) {
          return createErrorResponse("customer_number is required", 400, corsHeaders);
        }
        return createJsonResponse(
          await cj.callJson(`/api/Contact/byCustomerNumber/${seg(customer_number)}`),
          corsHeaders,
        );
      }

      case "equipment": {
        const { page = 1, pageSize = 100 } = body;
        return createJsonResponse(
          await cj.callJson(
            `/api/Equipment/AllActive?page=${Number(page)}&pageSize=${Number(pageSize)}`,
          ),
          corsHeaders,
        );
      }

      /* One machine plus its meters — the shape a fleet assessment needs. Serial and
         equipment number are both accepted because dealers key on whichever their
         own records carry. */
      case "equipment_detail": {
        const { serial_number, equipment_number } = body;
        if (!serial_number && !equipment_number) {
          return createErrorResponse(
            "serial_number or equipment_number is required",
            400,
            corsHeaders,
          );
        }
        const equipment = serial_number
          ? await cj.callJson<any>(`/api/Equipment/bySerialNumber/${seg(serial_number)}`)
          : await cj.callJson<any>(`/api/Equipment/byEquipmentNumber/${seg(equipment_number)}`);

        const meterPath = serial_number
          ? `/api/MeterReadings/EquipmentMetersBySerial/${seg(serial_number)}`
          : `/api/MeterReadings/EquipmentMetersByEqNo/${seg(equipment_number)}`;
        /* A machine with no meter definitions is normal, not an error — don't let it
           take the equipment record down with it. */
        let meters: any[] = [];
        try {
          meters = (await cj.callJson<any[]>(meterPath)) ?? [];
        } catch (e) {
          console.warn("meter lookup failed:", (e as Error).message);
        }

        return createJsonResponse({ equipment, ...summariseMeters(meters) }, corsHeaders);
      }

      /* Real page volume, per customer, over a window.
         Unlike the meter averages this returns populated numbers today, and the
         date range genuinely filters rather than reporting a lifetime counter — so
         it is the usable basis for sizing a fleet. Periods with no data come back
         as an empty array rather than zeros, which the caller should treat as "no
         data" and not as "no printing". */
      case "page_volumes": {
        const { customer_id, start_date, end_date, is_billed } = body;
        if (!customer_id || !start_date || !end_date) {
          return createErrorResponse(
            "customer_id, start_date and end_date are required (YYYY-MM-DD)",
            400,
            corsHeaders,
          );
        }
        const params = new URLSearchParams({ startDate: start_date, endDate: end_date });
        if (typeof is_billed === "boolean") params.set("isBilled", String(is_billed));
        const rows =
          (await cj.callJson<any[]>(
            `/api/PrintReleaf/customers/${seg(customer_id)}?${params.toString()}`,
          )) ?? [];
        return createJsonResponse(
          { items: rows, hasData: rows.length > 0 },
          corsHeaders,
        );
      }

      case "printreleaf_customers":
        return createJsonResponse(
          { items: await cj.callJson("/api/PrintReleaf/customers") },
          corsHeaders,
        );

      case "contracts": {
        const { customer_number } = body;
        const path = customer_number
          ? `/api/Contract/active/customer/${seg(customer_number)}`
          : "/api/Contract/active";
        return createJsonResponse({ items: await cj.paginate(path, 100, 20) }, corsHeaders);
      }

      case "item": {
        const { item_number } = body;
        if (!item_number) return createErrorResponse("item_number is required", 400, corsHeaders);
        /* Price and availability for one item — what a quote line needs to validate
           against e-automate before the order is pushed. */
        return createJsonResponse(
          await cj.callJson(`/api/Item/GetByItemNumber/${seg(item_number)}`),
          corsHeaders,
        );
      }

      /* Lookup lists, resolved by name around the 403 family — see the header note. */
      case "list": {
        const { list } = body;
        if (!list) return createErrorResponse("list is required", 400, corsHeaders);
        return createJsonResponse({ items: await cj.getList(list) }, corsHeaders);
      }

      default:
        return createErrorResponse(`Unknown action "${action}"`, 400, corsHeaders);
    }
  } catch (e) {
    const authzResp = authzErrorResponse(e, corsHeaders);
    if (authzResp) return authzResp;
    console.error("ceojuice-lookup:", (e as Error).message);
    return createErrorResponse((e as Error).message, 500, corsHeaders);
  }
});
