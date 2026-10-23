export const AUTH0_ROUTES = {
  login: "/auth/login",
  callback: "/auth/callback",
  logout: "/auth/logout",
  profile: "/auth/profile",
} as const;

const PUBLIC_PREFIXES = [
  "/login",
  "/signup",
  "/pricing",
  "/auth",
  "/api/auth",
  "/_next",
] as const;

export function isPublicPath(pathname: string): boolean {
  return PUBLIC_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function auth0LoginTarget(searchParams: URLSearchParams): string {
  const target = new URL(AUTH0_ROUTES.login, "http://fraudlens.local");
  if (searchParams.get("mode") === "signup") target.searchParams.set("screen_hint", "signup");
  const explicitReturnTo = searchParams.get("returnTo");
  const plan = searchParams.get("plan");
  if (explicitReturnTo?.startsWith("/") && !explicitReturnTo.startsWith("//")) {
    target.searchParams.set("returnTo", explicitReturnTo);
  } else if (plan && /^[a-z0-9_-]{1,32}$/i.test(plan)) {
    target.searchParams.set("returnTo", `/workspaces?plan=${encodeURIComponent(plan)}`);
  }
  return `${target.pathname}${target.search}`;
}
