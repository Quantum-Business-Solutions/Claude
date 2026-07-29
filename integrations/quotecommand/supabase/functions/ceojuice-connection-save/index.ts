/**
 * Save, test, and remove a dealer's CEO Juice credential.
 *
 * WHY SAVE AND TEST ARE THE SAME OPERATION. A stored credential that has never
 * been exercised is indistinguishable from a wrong one, and the moment a dealer
 * finds out is when a quote fails to push — long after they typed it. So `save`
 * logs in BEFORE it writes, and refuses to store a credential CEO Juice rejects.
 * There is no path here that persists an untested password.
 *
 * The login also yields the JWT's claims, which is the only way to show a dealer
 * WHICH e-automate tenant their credential actually reaches. A valid credential
 * bound to the wrong CustomerNumber is otherwise invisible until the data looks
 * subtly wrong, so the tenant is surfaced on save and stored for Settings.
 */

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createErrorResponse, createJsonResponse } from "../_shared/validation.ts";
import { authzErrorResponse, requireDealerAccess, requireDealerAdmin } from "../_shared/authz.ts";
import { ceoJuiceLogin, encryptSecret } from "../_shared/ceojuice-connection.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const KEY_ENV = "CEOJUICE_CREDENTIAL_ENCRYPTION_KEY";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  try {
    const body = await req.json();
    const { action, dealer_id, base_url, username, password } = body ?? {};

    if (!action) return createErrorResponse("Missing action", 400, corsHeaders);

    const caller = await requireDealerAccess(supabase, req, { dealer_id });

    /* Connecting an integration is an owner/admin decision, not a member one — it
       binds every quote this dealer pushes to one e-automate tenant. */
    if (action === "save" || action === "disconnect") requireDealerAdmin(caller);

    if (action === "status") {
      const { data } = await supabase
        .from("ceojuice_dealer_connections")
        .select(
          "base_url, username, api_key_id, customer_number, customer_name, last_connected_at, last_error, token_expires_at, updated_at",
        )
        .eq("dealer_id", caller.dealerId)
        .maybeSingle();

      /* Never return password_encrypted, and never the cached JWT — neither is
         needed to render status and both are credentials. */
      return createJsonResponse({ connected: Boolean(data), connection: data ?? null }, corsHeaders);
    }

    if (action === "save") {
      if (!base_url || !username || !password) {
        return createErrorResponse(
          "base_url, username and password are all required.",
          400,
          corsHeaders,
        );
      }
      if (!/^https:\/\//i.test(base_url)) {
        /* The credential is sent as a request body on every login. Over plain HTTP
           that is a password on the wire, so this is refused rather than warned
           about. */
        return createErrorResponse("base_url must be https.", 400, corsHeaders);
      }
      if (!Deno.env.get(KEY_ENV)) {
        return createErrorResponse(
          `${KEY_ENV} is not configured, so the password cannot be encrypted at rest. ` +
            "Generate one with `openssl rand -base64 32` and set it in edge-function secrets.",
          500,
          corsHeaders,
        );
      }

      /* Test before persisting — see the note at the top of this file. */
      let login;
      try {
        login = await ceoJuiceLogin(base_url, username, password);
      } catch (e) {
        return createErrorResponse((e as Error).message, 400, corsHeaders);
      }

      const password_encrypted = await encryptSecret(password, KEY_ENV);

      const { error } = await supabase
        .from("ceojuice_dealer_connections")
        .upsert(
          {
            dealer_id: caller.dealerId,
            base_url: base_url.replace(/\/+$/, ""),
            username,
            password_encrypted,
            access_token: login.token,
            token_expires_at: login.expiresAt,
            api_key_id: login.identity.apiKeyId,
            customer_number: login.identity.customerNumber,
            customer_name: login.identity.customerName,
            last_connected_at: new Date().toISOString(),
            last_error: null,
          },
          { onConflict: "dealer_id" },
        );
      if (error) return createErrorResponse(`Save failed: ${error.message}`, 500, corsHeaders);

      return createJsonResponse(
        {
          connected: true,
          /* Echoed so the dealer can confirm they are pointed at the tenant they
             expect before they push a single order. */
          tenant: {
            customerNumber: login.identity.customerNumber,
            customerName: login.identity.customerName,
            apiKeyId: login.identity.apiKeyId,
          },
          tokenExpiresAt: login.expiresAt,
        },
        corsHeaders,
      );
    }

    if (action === "disconnect") {
      const { error } = await supabase
        .from("ceojuice_dealer_connections")
        .delete()
        .eq("dealer_id", caller.dealerId);
      if (error) return createErrorResponse(`Disconnect failed: ${error.message}`, 500, corsHeaders);
      /* Push history is deliberately NOT deleted: it is the record of which quotes
         reached e-automate, and that stays true after the credential is removed. */
      return createJsonResponse({ connected: false }, corsHeaders);
    }

    return createErrorResponse(`Unknown action "${action}"`, 400, corsHeaders);
  } catch (e) {
    const authzResp = authzErrorResponse(e, corsHeaders);
    if (authzResp) return authzResp;
    console.error("ceojuice-connection-save:", (e as Error).message);
    return createErrorResponse((e as Error).message, 500, corsHeaders);
  }
});
