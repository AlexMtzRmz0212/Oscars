import { useEffect } from "react";

const SITE_NAME = "Every Envelope";

/** Names the page in the browser tab, and in the announcement screen readers make on navigation. */
export function usePageTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} | ${SITE_NAME}` : SITE_NAME;
  }, [title]);
}
