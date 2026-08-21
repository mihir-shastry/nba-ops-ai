"use client";

import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";

interface DataTableProps<T> {
  columns: ColumnDef<T, any>[];
  data: T[];
  height?: number;
  onRowClick?: (row: T) => void;
}

export default function DataTable<T>({
  columns,
  data,
  height = 500,
  onRowClick,
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<any[]>([]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div
      className="overflow-auto rounded-xl border border-court-border bg-court-card"
      style={{ maxHeight: height }}
    >
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-court-card z-10">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-court-muted font-semibold text-xs uppercase tracking-wider border-b border-court-border cursor-pointer select-none hover:text-white"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center gap-1">
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                    {{
                      asc: <ChevronUp size={14} />,
                      desc: <ChevronDown size={14} />,
                    }[header.column.getIsSorted() as string] ?? null}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className={`border-b border-court-border hover:bg-white/5 ${
                onRowClick ? "cursor-pointer" : ""
              }`}
              onClick={() => onRowClick?.(row.original)}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
