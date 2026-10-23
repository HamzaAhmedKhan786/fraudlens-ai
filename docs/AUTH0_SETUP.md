# Auth0 configuration

FraudLens uses `@auth0/nextjs-auth0` v4 with Next.js 16 `proxy.ts`. The SDK owns encrypted
browser sessions and the `/auth/*` protocol routes. The legacy `/api/auth/login` and
`/api/auth/logout` endpoints remain compatibility redirects; the provider-neutral callback remains
available only when Auth0 is not configured.

## Auth0 application settings

For the standard local URL `http://localhost:3000`, configure the Auth0 **Regular Web Application**:

- Allowed Callback URLs: `http://localhost:3000/auth/callback`
- Allowed Logout URLs: `http://localhost:3000`, `http://localhost:3000/login`
- Allowed Web Origins: `http://localhost:3000`

For production, add only the real HTTPS equivalents:

- `https://<your-app-domain>/auth/callback`
- `https://<your-app-domain>` and `https://<your-app-domain>/login`

If the app is deliberately run on `127.0.0.1`, port `3001`, or a preview hostname, that exact
origin and `/auth/callback` must be registered and must match `APP_BASE_URL`. Do not add wildcard
production callbacks. The Google connector callback is separate and remains
`http://localhost:8000/api/v1/connectors/google/callback` for local development.

## Auth0 API and token claims

Create an Auth0 API whose Identifier exactly matches `AUTH0_AUDIENCE` in the Next.js service and
`OIDC_AUDIENCE` in FastAPI. Use **RS256** and enable **Allow Offline Access** on that API so the
SDK can renew access tokens without forcing users to sign in again. Configure FastAPI with:

```dotenv
OIDC_ENABLED=true
OIDC_ISSUER=https://your-tenant.eu.auth0.com/
OIDC_AUDIENCE=https://api.fraudlens.example
OIDC_JWKS_URL=https://your-tenant.eu.auth0.com/.well-known/jwks.json
OIDC_ALGORITHM=RS256
OIDC_TENANT_CLAIM=https://fraudlens.example/tenant_id
OIDC_ROLES_CLAIM=https://fraudlens.example/roles
```

The URLs above are placeholders. Use the exact domain and API Identifier shown in the Auth0
Dashboard. Keep the trailing slash on `OIDC_ISSUER`.

Auth0 must issue the configured tenant and roles claims in the **access token**. Add a post-login
Auth0 Action that reads an internal FraudLens tenant ID from trusted Auth0 app metadata (or a
validated Auth0 Organization mapping) and adds namespaced custom claims. Roles must be a subset of
`admin`, `analyst`, `reviewer`, `viewer`, and `executive`. Never accept tenant or role values from
user-editable metadata. The internal membership table remains authoritative when a user switches
workspaces; a token cannot grant access to another workspace without an active membership.

Example Action logic (replace the namespace only if the matching environment variables change):

```js
exports.onExecutePostLogin = async (event, api) => {
  const tenantId = event.user.app_metadata?.fraudlens_tenant_id;
  const roles = event.authorization?.roles ?? [];
  if (tenantId) {
    api.accessToken.setCustomClaim("https://fraudlens.example/tenant_id", tenantId);
  }
  api.accessToken.setCustomClaim("https://fraudlens.example/roles", roles);
};
```

## Next.js variables

Copy placeholders from `apps/web/.env.example`. `AUTH0_SECRET` encrypts SDK session and transaction
cookies and must be a unique 32-byte hexadecimal secret. `AUTH0_CLIENT_SECRET`, `AUTH0_SECRET`, and
access tokens are server-only. The browser receives only encrypted, HTTP-only session cookies.

The actual routes are:

| Purpose | Route |
| --- | --- |
| Login | `/auth/login` |
| Signup | `/auth/login?screen_hint=signup` |
| Callback | `/auth/callback` |
| Logout | `/auth/logout` |
| SDK profile | `/auth/profile` |

## Manual verification

1. Start FastAPI and Next.js with matching audience/issuer settings.
2. Visit `/login`, complete Universal Login, and confirm return to `/`.
3. Confirm `/api/v1/session` resolves the expected tenant and role through the BFF.
4. Switch to a second workspace where the same subject has an active membership; then try an
   unassigned workspace and confirm `403 Workspace membership required`.
5. Sign out and verify both the local encrypted session and Auth0 session are cleared.

Automated tests validate route mapping, open-redirect rejection, JWT issuer/audience/algorithm,
required claims, role filtering, and cross-tenant membership enforcement. Universal Login itself
requires a real browser and the manually configured Auth0 tenant.
