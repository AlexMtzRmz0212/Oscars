import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { filmHref } from "../../lib/archive";
import { formatCount, plural } from "../../lib/format";
import { Poster } from "../../components/Poster";
import type { SweepCell } from "../../lib/types";
import "./SeatEnvelope.css";

interface Props {
  cell: SweepCell | null;
  onClose: () => void;
}

/** The live element: opening a seat pulls its card out of a gold envelope. */
export function SeatEnvelope({ cell, onClose }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (cell && !dialog.open) dialog.showModal();
    if (!cell && dialog.open) dialog.close();
  }, [cell]);

  const hidden = cell ? cell.count - cell.films.length : 0;

  return (
    <dialog
      ref={dialogRef}
      className="seat-envelope"
      aria-labelledby="seat-envelope-title"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      {cell && (
        <div className="seat-envelope-body" key={`${cell.nominations}:${cell.wins}`}>
          <div className="seat-card">
            <div className="seat-card-head">
              <h2 id="seat-envelope-title">
                {plural(cell.nominations, "nomination")}, {plural(cell.wins, "win")}
              </h2>
              <button type="button" className="button seat-card-close" onClick={onClose}>
                Close
              </button>
            </div>
            <p className="seat-card-count">{plural(cell.count, "film")} in this seat</p>
            <ul className="seat-card-films">
              {cell.films.map((film) => (
                <li key={film.id}>
                  {film.poster ? (
                    <Poster path={film.poster} alt="" sizes="44px" />
                  ) : (
                    <span className="seat-card-no-poster" />
                  )}
                  <Link className="seat-card-title" to={filmHref(film.id)}>
                    {film.title}
                  </Link>
                  <span className="seat-card-year">{film.year}</span>
                </li>
              ))}
            </ul>
            {hidden > 0 && (
              <p className="seat-card-more">
                Showing the {formatCount(cell.films.length)} most recent of {formatCount(cell.count)}.
              </p>
            )}
          </div>
          <div className="seat-pocket" aria-hidden="true" />
        </div>
      )}
    </dialog>
  );
}
