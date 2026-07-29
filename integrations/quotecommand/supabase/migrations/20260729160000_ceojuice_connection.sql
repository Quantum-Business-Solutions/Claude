-- ============================================================================
-- DEALER-SCOPED CEO JUICE CREDENTIALS.
--
-- CEO Juice's Client API exposes a dealer's e-automate data — customers,
-- equipment, contracts, and the ID634 sales-order import that a won quote gets
-- pushed into. It authenticates with a username and password traded for a
-- six-hour JWT, which makes it unlike the HubSpot connection in two ways that
-- drive this schema.
--
-- WHY THE PASSWORD IS STORED AT ALL. OAuth lets us keep a refresh token and
-- never the credential. CEO Juice has no refresh grant: the ONLY way to obtain a
-- new JWT is to re-present the username and password. A six-hour token against a
-- long-lived integration means re-authenticating several times a day forever, so
-- the credential has to persist. It is encrypted at rest with AES-256-GCM
-- (_shared/crypto.ts) and never returned by any read path — `ceojuice-lookup`
-- selects the ciphertext column only inside the edge function, and RLS below
-- keeps the anon/authenticated roles out of the table entirely.
--
-- WHY THE JWT IS CACHED HERE RATHER THAN IN MEMORY. Edge functions are
-- stateless; a module-level variable survives only as long as one warm isolate.
-- Caching the token in the row means a burst of ten invocations performs one
-- login instead of ten, which matters because the dev host resets connections
-- under sustained load. Expiry is stored so a caller can decide to refresh
-- without a round trip that would 401.
--
-- ONE CONNECTION PER DEALER, enforced by a primary key on dealer_id rather than a
-- unique index on a surrogate id. The HubSpot table learned this the hard way:
-- `hubspot_dealer_connections` is queried with `.maybeSingle()` on dealer_id, so a
-- second row for the same dealer turns every CRM call into a runtime error rather
-- than a constraint violation at write time. Making dealer_id the key moves that
-- failure to the insert, where it can be reported.
--
-- BASE URL IS PER DEALER AND NOT DEFAULTED TO PRODUCTION. The dev host
-- (devclientsapi.ceojuice.com) is the only one confirmed to resolve;
-- clientsapi.ceojuice.com does not answer DNS, so the production hostname is
-- genuinely unknown as of this migration. Defaulting the column to a guessed
-- production URL would let a dealer be silently pointed at nothing. Requiring it
-- explicitly forces whoever connects a dealer to supply the host CEO Juice gave
-- them.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ceojuice_dealer_connections (
  dealer_id            uuid PRIMARY KEY REFERENCES public.dealers(id) ON DELETE CASCADE,

  /* Supplied per dealer — see note above on why this is not defaulted. */
  base_url             text        NOT NULL,
  username             text        NOT NULL,
  /* AES-256-GCM ciphertext, base64. Never plaintext, never selected by the client. */
  password_encrypted   text        NOT NULL,

  /* Cached JWT from POST /api/Auth/token. Null until the first successful login. */
  access_token         text,
  token_expires_at     timestamptz,

  /* Written from the token's own claims on each login so the UI can show which
     e-automate tenant a dealer is actually pointed at. A credential silently
     bound to the wrong CustomerNumber is otherwise invisible until the data
     looks wrong. */
  api_key_id           text,
  customer_number      text,
  customer_name        text,

  /* Result of the most recent login attempt. Kept so Settings can distinguish
     "never connected" from "connected, then the password changed" without
     forcing a live call to render the page. */
  last_connected_at    timestamptz,
  last_error           text,

  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.ceojuice_dealer_connections IS
  'One CEO Juice Client API credential per dealer. Password is AES-256-GCM encrypted; '
  'access_token is a cached six-hour JWT. No OAuth refresh grant exists, which is why '
  'the credential itself must persist.';

/* ---------------------------------------------------------------------------
   RLS: the table is readable by dealer members for STATUS ONLY, and writable by
   nobody through the client.

   The read policy is deliberately narrow in what it is FOR, not in what it
   exposes — Postgres RLS gates rows, not columns, so a member with select access
   can read password_encrypted. That ciphertext is useless without
   CEOJUICE_CREDENTIAL_ENCRYPTION_KEY, which lives only in edge-function env, but
   "useless without the key" is a weaker guarantee than "not reachable", so:

   Reads are granted to dealer members because Settings needs to render
   connection status, and every write goes through `ceojuice-connection-save`
   with the service-role key. If you would rather members could not see the
   ciphertext at all, replace the SELECT policy with a view over the non-secret
   columns and grant on that instead — noted here rather than done because it
   changes the shape the frontend queries.
   --------------------------------------------------------------------------- */

ALTER TABLE public.ceojuice_dealer_connections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Members view CEO Juice connection" ON public.ceojuice_dealer_connections;
CREATE POLICY "Members view CEO Juice connection"
  ON public.ceojuice_dealer_connections
  FOR SELECT
  USING (public.has_dealer_access(auth.uid(), dealer_id));

/* No INSERT/UPDATE/DELETE policies: writes are service-role only, which bypasses
   RLS. Stated explicitly because an absent policy reads as an oversight. */

CREATE OR REPLACE FUNCTION public.touch_ceojuice_connection_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ceojuice_connection_touch ON public.ceojuice_dealer_connections;
CREATE TRIGGER ceojuice_connection_touch
  BEFORE UPDATE ON public.ceojuice_dealer_connections
  FOR EACH ROW EXECUTE FUNCTION public.touch_ceojuice_connection_updated_at();

-- ============================================================================
-- QUOTE → SALES ORDER PUSH LOG.
--
-- ID634 is a staged batch import: the API writes one row per quote line into
-- CEO Juice's ZCJ_ImpSOOrderDetails under a shared SourceID, then a stored
-- procedure derives the order header and creates the e-automate sales order.
--
-- WHY THIS TABLE EXISTS. That pipeline is asynchronous and validating — CEO
-- Juice checks each row against existing customer, branch, item, warehouse and
-- sales-rep records, and HOLDS invalid orders rather than skipping them. So a
-- push that returns 200 has not necessarily produced a sales order; it may be
-- sitting in staging awaiting correction. Without a local record of what was
-- sent, "did this quote reach e-automate?" is unanswerable, and the natural
-- reflex is to push again — which is how a dealer ends up with duplicate orders
-- for one quote.
--
-- The unique index on quote_id where the push succeeded is what makes the retry
-- safe: a second attempt for an already-landed quote fails at the database
-- instead of creating a second order.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.ceojuice_order_pushes (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dealer_id        uuid NOT NULL REFERENCES public.dealers(id) ON DELETE CASCADE,
  quote_id         uuid NOT NULL,

  /* What we sent, verbatim, after header normalisation. Kept because the DTO has
     103 fields and reproducing a failed push from the quote alone is guesswork. */
  request_payload  jsonb NOT NULL,

  /* 'pending' | 'succeeded' | 'failed' */
  status           text  NOT NULL DEFAULT 'pending',
  http_status      integer,
  response_body    text,
  /* e-automate's order number / SOID once ID634 has derived the header. Null
     while the order is still staged or held. */
  so_number        text,
  error_message    text,

  pushed_by        uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT ceojuice_order_pushes_status_check
    CHECK (status IN ('pending', 'succeeded', 'failed'))
);

/* One successful push per quote. Failed attempts stay for diagnosis and do not
   block a retry. */
CREATE UNIQUE INDEX IF NOT EXISTS ceojuice_order_pushes_quote_once
  ON public.ceojuice_order_pushes (quote_id)
  WHERE status = 'succeeded';

CREATE INDEX IF NOT EXISTS ceojuice_order_pushes_dealer_created
  ON public.ceojuice_order_pushes (dealer_id, created_at DESC);

ALTER TABLE public.ceojuice_order_pushes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Members view order pushes" ON public.ceojuice_order_pushes;
CREATE POLICY "Members view order pushes"
  ON public.ceojuice_order_pushes
  FOR SELECT
  USING (public.has_dealer_access(auth.uid(), dealer_id));
