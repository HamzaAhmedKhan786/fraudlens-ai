import { describe, expect, it } from "vitest";
import { AUTH0_ROUTES, auth0LoginTarget, isPublicPath } from "./auth-routes";

describe("Auth0 route compatibility", () => {
  it("uses the SDK's Next.js 16 routes", () => {
    expect(AUTH0_ROUTES).toEqual({
      login: "/auth/login",
      callback: "/auth/callback",
      logout: "/auth/logout",
      profile: "/auth/profile",
    });
  });

  it("maps legacy login and signup links without an open redirect", () => {
    expect(auth0LoginTarget(new URLSearchParams())).toBe("/auth/login");
    expect(auth0LoginTarget(new URLSearchParams("mode=signup&plan=small"))).toBe(
      "/auth/login?screen_hint=signup&returnTo=%2Fworkspaces%3Fplan%3Dsmall",
    );
    expect(auth0LoginTarget(new URLSearchParams("returnTo=https://evil.example"))).toBe(
      "/auth/login",
    );
    expect(auth0LoginTarget(new URLSearchParams("returnTo=//evil.example"))).toBe(
      "/auth/login",
    );
  });

  it("keeps only authentication and marketing routes public", () => {
    expect(isPublicPath("/auth/callback")).toBe(true);
    expect(isPublicPath("/api/auth/login")).toBe(true);
    expect(isPublicPath("/pricing")).toBe(true);
    expect(isPublicPath("/cases")).toBe(false);
    expect(isPublicPath("/authenticated-admin")).toBe(false);
    expect(isPublicPath("/api/authentication-settings")).toBe(false);
  });
});
