export const annualDiscountPercent = 18;
export const plans = [
  { id:"individual", name:"Individual", monthly:9.99, users:"1", emails:"100", documents:"20", audience:"Private workspace for personal verification" },
  { id:"small", name:"Small Business", monthly:49, users:"5", emails:"1,000", documents:"100", audience:"Shared fraud triage for small teams" },
  { id:"pro", name:"Business Pro", monthly:149, users:"20", emails:"5,000", documents:"500", audience:"Higher-volume investigations and collaboration" },
  { id:"enterprise", name:"Enterprise", monthly:499, users:"Custom", emails:"Custom", documents:"Custom", audience:"Advanced integrations, controls, and support" },
] as const;
