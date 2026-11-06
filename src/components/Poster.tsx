import { posterSrcSet, posterUrl } from "../lib/posters";

interface Props {
  path: string;
  /** Empty when a visible title beside the poster already names the film. */
  alt: string;
  /** How wide the poster displays, in the format of the HTML sizes attribute. */
  sizes: string;
  className?: string;
  /** For the main image on a page: loads first instead of when scrolled near. */
  priority?: boolean;
}

/** Offers every size TMDB has, so the browser picks the sharpest one the screen can show. */
export function Poster({ path, alt, sizes, className, priority }: Props) {
  return (
    <img
      className={className}
      src={posterUrl(path, "w342")}
      srcSet={posterSrcSet(path)}
      sizes={sizes}
      alt={alt}
      width={500}
      height={750}
      fetchPriority={priority ? "high" : undefined}
      loading={priority ? undefined : "lazy"}
      decoding="async"
    />
  );
}
