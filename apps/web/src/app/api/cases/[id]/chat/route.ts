import{backendFetch}from"@/lib/backend";
export async function GET(_:Request,{params}:{params:Promise<{id:string}>}){const{id}=await params;return Response.json(await backendFetch(`/cases/${encodeURIComponent(id)}/chat`))}
export async function POST(request:Request,{params}:{params:Promise<{id:string}>}){const{id}=await params;try{return Response.json(await backendFetch(`/cases/${encodeURIComponent(id)}/chat`,{method:"POST",body:JSON.stringify(await request.json())}),{status:201})}catch(error){return Response.json({detail:error instanceof Error?error.message:"Copilot failed"},{status:502})}}
