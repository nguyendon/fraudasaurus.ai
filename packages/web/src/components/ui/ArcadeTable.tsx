"use client";

import { motion } from "framer-motion";

interface Column<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  className?: string;
}

interface ArcadeTableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
}

export function ArcadeTable<T extends object>({
  data,
  columns,
  className = "",
}: ArcadeTableProps<T>) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <motion.table
        className="arcade-table w-full text-[8px] sm:text-xs"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
      >
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={`text-left uppercase whitespace-nowrap ${col.className || ""}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <motion.tr
              key={rowIndex}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: rowIndex * 0.1 }}
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={`whitespace-nowrap ${col.className || ""}`}
                >
                  {col.render
                    ? col.render(row[col.key], row)
                    : String(row[col.key])}
                </td>
              ))}
            </motion.tr>
          ))}
        </tbody>
      </motion.table>
    </div>
  );
}
