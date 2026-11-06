import { motion } from "motion/react";
import type { ReactNode } from "react";
import { rise, riseAfter } from "../lib/motion";
import { useIdle } from "../lib/useIdle";
import { useStoryData } from "../lib/useStoryData";
import "./Act.css";

export type Field = "velvet" | "oxblood" | "curtain" | "gold" | "ivory";

interface ActProps<Data> {
  id: string;
  title: string;
  note: string;
  field: Field;
  dataName: string;
  facts?: (data: Data) => [string, string][];
  children: (data: Data) => ReactNode;
}

/** One act of the show: a title card on its own field of colour, then its chart on velvet. */
export function Act<Data>({ id, title, note, field, dataName, facts, children }: ActProps<Data>) {
  const story = useStoryData<Data>(dataName);
  const idle = useIdle();
  const titleId = `${id}-title`;

  return (
    <section className="act" id={id} aria-labelledby={titleId}>
      <div className={`act-card field-${field}`}>
        <div className="act-heading">
          <motion.h2 id={titleId} {...rise}>
            {title}
          </motion.h2>
          <motion.p className="act-note" {...riseAfter(1)}>
            {note}
          </motion.p>
        </div>
        {story.status === "ready" && facts && (
          <dl className="act-facts">
            {facts(story.data).map(([value, label], index) => (
              <motion.div key={label} {...riseAfter(index)}>
                <dt>{value}</dt>
                <dd>{label}</dd>
              </motion.div>
            ))}
          </dl>
        )}
      </div>

      <div className="act-body">
        {story.status === "loading" && <p className="act-status">Seating the house…</p>}
        {story.status === "error" && (
          <p className="act-status" role="alert">
            This act didn’t load. Refresh the page to try again.
          </p>
        )}
        {story.status === "ready" && idle && children(story.data)}
      </div>
    </section>
  );
}
