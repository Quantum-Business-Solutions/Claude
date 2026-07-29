# Patch: generalize `_shared/crypto.ts` to hold more than one secret

`crypto.ts` today reads its key from a hard-coded env var:

```ts
const keyBase64 = Deno.env.get('HUBSPOT_TOKEN_ENCRYPTION_KEY');
```

That is correct for HubSpot tokens and wrong as a general secret store. The CEO
Juice connection has to persist a **password**, not a refresh token — there is no
OAuth refresh grant, so the credential itself is the only way to renew a JWT —
and encrypting a CEO Juice password under a variable named
`HUBSPOT_TOKEN_ENCRYPTION_KEY` conflates two independent secrets. Rotating the
HubSpot key would then silently invalidate every dealer's CEO Juice credential,
and the failure would surface as "CEO Juice rejected the password" long after the
rotation, pointing at the wrong cause.

So: add an optional key-name argument. Existing behaviour is the default, so **no
call site changes and no re-encryption of stored HubSpot tokens.**

## The change

Replace the `getEncryptionKey` signature and add two aliases at the end of the
file. Nothing else in `crypto.ts` moves.

```ts
async function getEncryptionKey(
  envVar = 'HUBSPOT_TOKEN_ENCRYPTION_KEY',
): Promise<CryptoKey> {
  const keyBase64 = Deno.env.get(envVar);
  if (!keyBase64) {
    throw new Error(`${envVar} not configured`);
  }
  // ...rest of the function unchanged
}

export async function encryptToken(
  plaintext: string,
  envVar?: string,
): Promise<string> {
  const key = await getEncryptionKey(envVar);
  // ...rest unchanged
}

export async function decryptToken(
  encrypted: string,
  envVar?: string,
): Promise<string> {
  const key = await getEncryptionKey(envVar);
  // ...rest unchanged
}

/* Named for what they hold rather than for HubSpot. `encryptToken` is kept as the
   name every existing caller already uses; these are the same function under a
   name that does not imply an OAuth token. */
export const encryptSecret = encryptToken;
export const decryptSecret = decryptToken;
```

Both aliases take `(value, envVar?)`, which is what
`ceojuice-connection.ts` calls with `"CEOJUICE_CREDENTIAL_ENCRYPTION_KEY"`.

## Why aliases rather than renaming

`encryptToken` appears across the HubSpot OAuth path. Renaming it is a wide
mechanical diff with no behavioural payoff, and it would collide with any
in-flight branch touching those files. The aliases give the CEO Juice code an
honest name at the cost of two lines.

## Generating the new key

```bash
openssl rand -base64 32
```

Set it as `CEOJUICE_CREDENTIAL_ENCRYPTION_KEY` in Supabase edge-function secrets.
It must decode to exactly 32 bytes — `getEncryptionKey` already checks and throws
a clear error if not.

## Note on `isEncryptedToken`

That helper decides "is this ciphertext?" partly by checking the value does not
start with `eyJ`, since a plaintext JWT does. It is a migration-period heuristic
for HubSpot tokens and is **not** used by the CEO Juice path — the password column
is encrypted from the first write, so there is no mixed-state period to detect.
Leave it alone.
