import { Link } from "react-router-dom";
import "./Footer.css";

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer-notes">
        <p>
          Every Envelope is an independent, non-commercial project. It is not affiliated with or endorsed by the
          Academy of Motion Picture Arts and Sciences. “Oscar” and “Academy Awards” are the Academy’s trademarks.
        </p>
        <p>
          Nominations data:{" "}
          <a href="https://github.com/DLu/oscar_data" rel="noreferrer">
            DLu/oscar_data
          </a>
          , BSD 2-Clause licence. Counts cover competitive categories and exclude honorary and Sci-Tech awards.
        </p>
        <p>
          Posters, money, scores and languages: TMDB. This product uses the TMDB API but is not endorsed or certified by
          TMDB. Birth years and gender: Wikidata. Inflation: US Bureau of Labor Statistics CPI-U.{" "}
          <Link to="/methods">How every number is made</Link>.
        </p>
      </div>
      <div className="site-footer-inner">
        <p className="site-footer-name" aria-hidden="true">
          Every Envelope
        </p>
      </div>
    </footer>
  );
}
