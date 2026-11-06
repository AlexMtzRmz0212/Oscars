import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { filmHref } from "../lib/archive";
import { rise } from "../lib/motion";
import { Poster } from "../components/Poster";
import type { FilmSummary } from "../lib/types";
import "./ScrollStory.css";

export interface StorySlip {
  id: string;
  heading: string;
  body: string;
  /** Posters tipped onto the slip, like plates in a printed programme. */
  plates?: FilmSummary[];
}

/** A slip takes over when its top passes this far down the screen, which clears the pinned chart on a phone. */
const TRIGGER_LINE = 0.68;

interface Props<Slip extends StorySlip> {
  slips: Slip[];
  renderStage: (slip: Slip) => ReactNode;
}

/** A pinned chart with printed slips passing beside it. The slip at the trigger line drives the chart. */
export function ScrollStory<Slip extends StorySlip>({ slips, renderStage }: Props<Slip>) {
  const [activeIndex, setActiveIndex] = useState(0);
  const storyRef = useRef<HTMLDivElement>(null);
  const slipRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    let frame = 0;

    // Read from position, not crossings, so a fast scroll or a programme link still lands on the right step.
    const update = () => {
      frame = 0;
      const story = storyRef.current?.getBoundingClientRect();
      if (!story || story.bottom < 0 || story.top > window.innerHeight) return;
      const line = window.innerHeight * TRIGGER_LINE;
      let active = 0;
      slipRefs.current.forEach((slip, index) => {
        if (slip && slip.getBoundingClientRect().top < line) active = index;
      });
      setActiveIndex(active);
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [slips]);

  return (
    <div className="story" ref={storyRef}>
      <div className="story-stage">{renderStage(slips[activeIndex])}</div>
      <div className="story-slips">
        {slips.map((slip, index) => (
          <motion.div key={slip.id} className="slip-holder" {...rise}>
            <article
              className="slip"
              data-step={index}
              data-active={index === activeIndex}
              ref={(element) => {
                slipRefs.current[index] = element;
              }}
            >
              <h3>{slip.heading}</h3>
              <p>{slip.body}</p>
              {slip.plates && slip.plates.length > 0 && (
                <ul className={slip.plates.length > 3 ? "slip-plates slip-plates-dense" : "slip-plates"}>
                  {slip.plates.map(
                    (film) =>
                      film.poster && (
                        <li key={film.id}>
                          <Link to={filmHref(film.id)}>
                            <Poster path={film.poster} alt={`Poster for ${film.title}`} sizes="(max-width: 900px) 30vw, 130px" />
                          </Link>
                        </li>
                      ),
                  )}
                </ul>
              )}
            </article>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
