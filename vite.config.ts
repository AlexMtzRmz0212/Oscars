import { defineConfig } from "vite";
import type { Plugin } from "vite";
import react from "@vitejs/plugin-react";

const CRITICAL_FONTS = [/bebas-neue-latin-400-normal.*\.woff2$/, /eb-garamond-latin-400-normal.*\.woff2$/];

/** Vite gives fonts hashed names, so their preload links can only be written after the build. */
function preloadCriticalFonts(): Plugin {
  return {
    name: "preload-critical-fonts",
    transformIndexHtml: {
      order: "post",
      handler(_html, context) {
        const names = Object.keys(context.bundle ?? {});
        const fonts = names.filter((file) => CRITICAL_FONTS.some((font) => font.test(file)));
        const show = names.find((file) => /TheShow-.*\.js$/.test(file));
        return [
          ...fonts.map((file) => ({
            tag: "link",
            attrs: { rel: "preload", as: "font", type: "font/woff2", href: `/${file}`, crossorigin: "" },
            injectTo: "head" as const,
          })),
          // The show's code is the home page's content, so only that page fetches it early.
          ...(show
            ? [
                {
                  tag: "script",
                  children: `if(location.pathname==="/"){var l=document.createElement("link");l.rel="modulepreload";l.href=${JSON.stringify(`/${show}`)};document.head.appendChild(l)}`,
                  injectTo: "head" as const,
                },
              ]
            : []),
        ];
      },
    },
  };
}

export default defineConfig({
  base: "/",
  plugins: [react(), preloadCriticalFonts()],
});
