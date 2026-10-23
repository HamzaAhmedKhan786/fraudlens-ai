import { NextRequest, NextResponse } from "next/server";
import { AUTH0_ROUTES, isPublicPath } from "@/lib/auth-routes";
import { getAuth0, isAuth0Configured } from "@/lib/auth0";

export async function proxy(request: NextRequest) {
  if (process.env.OIDC_ENABLED !== "true") return NextResponse.next();

  if (isAuth0Configured()) {
    const auth0 = getAuth0();
    const response = await auth0.middleware(request);
    if (isPublicPath(request.nextUrl.pathname)) return response;
    if (!await auth0.getSession(request)) {
      const login = new URL(AUTH0_ROUTES.login, request.url);
      login.searchParams.set("returnTo", `${request.nextUrl.pathname}${request.nextUrl.search}`);
      return NextResponse.redirect(login);
    }
    // Refresh early-expiring access tokens in middleware so updated encrypted
    // session cookies are persisted before Server Components call FastAPI.
    try {
      await auth0.getAccessToken(request, response);
    } catch {
      const login = new URL(AUTH0_ROUTES.login, request.url);
      login.searchParams.set("returnTo", `${request.nextUrl.pathname}${request.nextUrl.search}`);
      return NextResponse.redirect(login);
    }
    return response;
  }

  if (!isPublicPath(request.nextUrl.pathname) && !request.cookies.get("fraudlens_session")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|brand/).*)"],
};
