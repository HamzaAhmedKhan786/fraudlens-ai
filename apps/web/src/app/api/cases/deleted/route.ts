import{backendFetch}from"@/lib/backend";export async function GET(){return Response.json(await backendFetch("/cases-deleted"))}
