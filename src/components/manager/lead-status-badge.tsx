import { LeadStatus } from "@/lib/types";

const statusMap: Record<LeadStatus, string> = {
  new: "bg-slate-100 text-slate-700",
  in_review: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-700"
};

const labelMap: Record<LeadStatus, string> = {
  new: "New",
  in_review: "In review",
  approved: "Approved",
  rejected: "Rejected"
};

export function LeadStatusBadge({ status }: { status: LeadStatus }) {
  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusMap[status]}`}>{labelMap[status]}</span>;
}
