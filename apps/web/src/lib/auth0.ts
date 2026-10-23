import "server-only";
import { Auth0Client } from "@auth0/nextjs-auth0/server";

export function isAuth0Configured(): boolean {
  return process.env.OIDC_ENABLED === "true" && Boolean(
    process.env.AUTH0_DOMAIN &&
    process.env.AUTH0_CLIENT_ID &&
    process.env.AUTH0_CLIENT_SECRET &&
    process.env.AUTH0_SECRET &&
    (process.env.AUTH0_AUDIENCE || process.env.OIDC_AUDIENCE),
  );
}

let client: Auth0Client | undefined;

export function getAuth0(): Auth0Client {
  if (!isAuth0Configured()) throw new Error("Auth0 is not configured");
  if (!client) {
    client = new Auth0Client({
      authorizationParameters: {
        scope: process.env.AUTH0_SCOPE || "openid profile email offline_access",
        audience: process.env.AUTH0_AUDIENCE || process.env.OIDC_AUDIENCE,
      },
      enableAccessTokenEndpoint: false,
      tokenRefreshBuffer: 60,
      session: {
        rolling: true,
        inactivityDuration: 60 * 60,
        absoluteDuration: 8 * 60 * 60,
      },
    });
  }
  return client;
}
