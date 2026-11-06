import { motion, useReducedMotion } from "motion/react";
import { useState } from "react";
import "./Curtain.css";

const SEEN_KEY = "every-envelope:curtain-seen";

/** Flat pleats, varied in width and tone like real fabric folds. */
const PLEATS = [7, 11, 6, 9, 13, 7, 10, 8, 12, 6, 11];
const PLEAT_TONES = ["var(--curtain)", "var(--curtain-deep)", "var(--curtain-lit)", "var(--curtain-deep)"];

function hasSeenCurtain() {
  try {
    return sessionStorage.getItem(SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

function markCurtainSeen() {
  try {
    sessionStorage.setItem(SEEN_KEY, "1");
  } catch {
    // Without storage the curtain simply rises again next visit.
  }
}

function Panel({ side, onOpened }: { side: "left" | "right"; onOpened?: () => void }) {
  return (
    <motion.div
      className={`curtain-panel curtain-panel-${side}`}
      initial={{ x: 0 }}
      animate={{ x: side === "left" ? "-101%" : "101%" }}
      transition={{ delay: 0.35, duration: 1.5, ease: [0.76, 0, 0.24, 1] }}
      onAnimationComplete={onOpened}
    >
      {PLEATS.map((width, index) => (
        <span key={index} style={{ flexGrow: width, background: PLEAT_TONES[index % PLEAT_TONES.length] }} />
      ))}
    </motion.div>
  );
}

/** Opens once per visit on first load. Skipped entirely when reduced motion is set. */
export function Curtain() {
  const reduced = useReducedMotion();
  const [open, setOpen] = useState(() => hasSeenCurtain());

  if (open || reduced) return null;

  return (
    <div className="curtain" aria-hidden="true">
      <Panel
        side="left"
        onOpened={() => {
          markCurtainSeen();
          setOpen(true);
        }}
      />
      <Panel side="right" />
    </div>
  );
}
