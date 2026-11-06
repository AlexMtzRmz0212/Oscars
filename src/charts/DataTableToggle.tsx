import { useState } from "react";
import type { ReactNode } from "react";
import "./DataTableToggle.css";

interface Props {
  summary: string;
  headers: string[];
  rows: ReactNode[][];
}

/** Every chart's values stay reachable without hover or sight, as a plain table, built only when opened. */
export function DataTableToggle({ summary, headers, rows }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <details className="data-table" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>{summary}</summary>
      {open && (
        <div className="data-table-scroll">
          <table>
            <thead>
              <tr>
                {headers.map((header) => (
                  <th key={header} scope="col">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((cells, rowIndex) => (
                <tr key={rowIndex}>
                  {cells.map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  );
}
