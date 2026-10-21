import { backendAuthHeaders, backendBaseUrl } from "@/lib/backend";

export async function GET(_request:Request,{params}:{params:Promise<{id:string}>}){
  const{id}=await params;
  const response=await fetch(`${backendBaseUrl}/cases/${encodeURIComponent(id)}/report`,{headers:await backendAuthHeaders(),cache:"no-store"});
  return new Response(await response.arrayBuffer(),{status:response.status,headers:{"Content-Type":response.headers.get("content-type")??"text/html","Content-Disposition":response.headers.get("content-disposition")??`attachment; filename="${id}-report.html"`}});
}
