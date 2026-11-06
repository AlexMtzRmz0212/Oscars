import { MotionConfig } from "motion/react";
import { Curtain } from "../components/Curtain";
import { Footer } from "../components/Footer";
import { useHashScroll } from "../lib/useHashScroll";
import { usePageTitle } from "../lib/usePageTitle";
import { Encore } from "./Encore";
import { Hero } from "./Hero";
import { Overture } from "./Overture";
import { Snubbed } from "./acts/Snubbed";
import { TheAudience } from "./acts/TheAudience";
import { TheFormula } from "./acts/TheFormula";
import { TheMoney } from "./acts/TheMoney";
import { TheProgramme } from "./acts/TheProgramme";
import { TheSweep } from "./acts/TheSweep";
import { WhoGetsTheGold } from "./acts/WhoGetsTheGold";

export default function TheShow() {
  usePageTitle();
  useHashScroll();
  return (
    <MotionConfig reducedMotion="user">
      <Curtain />
      <main id="main">
        <Hero />
        <Overture />
        <TheProgramme />
        <TheSweep />
        <TheFormula />
        <TheMoney />
        <TheAudience />
        <WhoGetsTheGold />
        <Snubbed />
        <Encore />
      </main>
      <Footer />
    </MotionConfig>
  );
}
