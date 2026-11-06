const WIDTHS = [92, 154, 185, 342, 500, 780] as const;

type PosterWidth = (typeof WIDTHS)[number];

/** Posters load from TMDb's image CDN and are not rehosted. */
export const posterUrl = (path: string, size: `w${PosterWidth}`) => `https://image.tmdb.org/t/p/${size}${path}`;

export const posterSrcSet = (path: string) => WIDTHS.map((width) => `${posterUrl(path, `w${width}`)} ${width}w`).join(", ");
