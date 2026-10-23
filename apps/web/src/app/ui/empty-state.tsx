import type { ReactNode } from "react";
export function EmptyState({ title, description, icon, action }: {
  title: string; description: string; icon?: ReactNode; action?: ReactNode;
}) {
  return <div className="flex min-h-40 flex-col items-center justify-center gap-3 p-6 text-center">
    {icon && <div className="text-brand">{icon}</div>}
    <h3 className="text-sm font-medium text-ink">{title}</h3>
    <p className="max-w-sm text-xs leading-relaxed text-muted">{description}</p>
    {action}
  </div>;
}
