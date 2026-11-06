import { motion, useMotionValue, useReducedMotion, useScroll, useTransform } from "motion/react";
import type { PointerEvent } from "react";
import { SiteBar } from "../components/SiteBar";
import { useStoryData } from "../lib/useStoryData";
import type { Meta } from "../lib/types";
import "./Hero.css";

export function Hero() {
  const reduced = useReducedMotion();
  const meta = useStoryData<Meta>("meta");
  const { scrollY } = useScroll();
  const flapAngle = useTransform(scrollY, [0, 420], [0, reduced ? 0 : 172]);

  const spotX = useMotionValue(-999);
  const spotY = useMotionValue(-999);

  function moveSpotlight(event: PointerEvent<HTMLElement>) {
    if (event.pointerType !== "mouse" || reduced) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    spotX.set(event.clientX - bounds.left);
    spotY.set(event.clientY - bounds.top);
  }

  return (
    <section className="hero" onPointerMove={moveSpotlight}>
      <motion.div className="hero-spotlight" style={{ x: spotX, y: spotY }} aria-hidden="true" />

      <SiteBar
        action={
          <a className="button hero-action" href="#overture">
            Begin the show
          </a>
        }
      />

      <motion.div
        className="envelope"
        initial={{ y: 56 }}
        animate={{ y: 0 }}
        transition={{ delay: 0.9, duration: 1.1, ease: [0.2, 0.8, 0.2, 1] }}
      >
        <motion.div className="envelope-flap" style={{ rotateX: flapAngle }} aria-hidden="true">
          <span className="envelope-seal" />
        </motion.div>
        <div className="envelope-face">
          <h1>
            Every
            <br />
            Envelope
          </h1>
          <p className="envelope-sub">Who won the Academy Awards, who didn’t, and why.</p>
          {meta.status === "ready" && (
            <p className="envelope-details">
              <span>{meta.data.ceremonies} ceremonies</span>
              <span className="diamond" aria-hidden="true" />
              <span>
                Films of {meta.data.firstFilmYear} to {meta.data.lastFilmYear}
              </span>
            </p>
          )}
        </div>
      </motion.div>
    </section>
  );
}
