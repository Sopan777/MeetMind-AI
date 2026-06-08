"use client";

import { useState } from "react";
import { Check, X, Clock } from "lucide-react";
import type { ActionItem } from "@/lib/mock-data";

const statusStyles: Record<string, string> = {
  todo: "bg-slate-500/20 text-slate-300",
  "in-progress": "bg-primary/20 text-primary-200",
  review: "bg-secondary/20 text-secondary-200",
  completed: "bg-emerald-500/20 text-emerald-300",
};

const priorityColors: Record<string, string> = {
  low: "bg-emerald-400",
  medium: "bg-amber-400",
  high: "bg-orange-400",
  critical: "bg-red-400",
};

interface ActionItemsTableProps {
  items: ActionItem[];
}

type SortKey = "task" | "owner" | "deadline" | "status" | "priority";

export default function ActionItemsTable({ items }: ActionItemsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("priority");
  const [sortAsc, setSortAsc] = useState(false);
  const [reviewStatuses, setReviewStatuses] = useState<Record<string, "pending" | "accepted" | "rejected">>(
    items.reduce((acc, item) => ({ ...acc, [item.id]: "pending" }), {})
  );

  const handleReview = (id: string, status: "accepted" | "rejected") => {
    setReviewStatuses((prev) => ({ ...prev, [id]: status }));
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  const sorted = [...items].sort((a, b) => {
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    const statusOrder = { todo: 0, "in-progress": 1, review: 2, completed: 3 };
    let cmp = 0;
    if (sortKey === "priority")
      cmp = priorityOrder[a.priority] - priorityOrder[b.priority];
    else if (sortKey === "status")
      cmp = statusOrder[a.status] - statusOrder[b.status];
    else if (sortKey === "deadline")
      cmp = new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
    else cmp = (a[sortKey] as string).localeCompare(b[sortKey] as string);
    return sortAsc ? cmp : -cmp;
  });

  const cols: { key: SortKey; label: string }[] = [
    { key: "task", label: "Task" },
    { key: "owner", label: "Owner" },
    { key: "deadline", label: "Deadline" },
    { key: "status", label: "Status" },
    { key: "priority", label: "Priority" },
    { key: "status" as SortKey, label: "Review" },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/5">
            {cols.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-4 py-3 cursor-pointer hover:text-white transition-colors"
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.03]">
          {sorted.map((item) => (
            <tr
              key={item.id}
              className="hover:bg-white/[0.02] transition-colors"
            >
              <td className="px-4 py-3">
                <span className="text-sm text-white">{item.task}</span>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-[9px] font-bold text-white">
                    {item.owner
                      .split(" ")
                      .map((w) => w[0])
                      .join("")}
                  </div>
                  <span className="text-sm text-slate-300">{item.owner}</span>
                </div>
              </td>
              <td className="px-4 py-3">
                <span className="text-sm text-slate-400">
                  {new Date(item.deadline).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={`badge ${statusStyles[item.status]}`}>
                  {item.status.replace("-", " ")}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${priorityColors[item.priority]}`}
                  />
                  <span className="text-sm text-slate-400 capitalize">
                    {item.priority}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3 text-right">
                {reviewStatuses[item.id] === "pending" ? (
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleReview(item.id, "accepted")}
                      className="p-1.5 rounded-md hover:bg-emerald-500/20 text-slate-400 hover:text-emerald-400 transition-colors"
                      title="Accept"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleReview(item.id, "rejected")}
                      className="p-1.5 rounded-md hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                      title="Reject"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : reviewStatuses[item.id] === "accepted" ? (
                  <span className="flex items-center justify-end gap-1 text-xs font-medium text-emerald-400">
                    <Check className="w-3.5 h-3.5" /> Accepted
                  </span>
                ) : (
                  <span className="flex items-center justify-end gap-1 text-xs font-medium text-red-400">
                    <X className="w-3.5 h-3.5" /> Rejected
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
