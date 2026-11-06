import { lazy, Suspense, useEffect } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";
import { ArchivePage, PageHead } from "./archive/parts";
import { usePageTitle } from "./lib/usePageTitle";
import { SearchProvider } from "./search/SearchContext";

const TheShow = lazy(() => import("./show/TheShow"));
const CeremoniesPage = lazy(() => import("./archive/CeremoniesPage"));
const CeremonyPage = lazy(() => import("./archive/CeremonyPage"));
const FilmPage = lazy(() => import("./archive/FilmPage"));
const PersonPage = lazy(() => import("./archive/PersonPage"));
const CategoriesPage = lazy(() => import("./archive/CategoriesPage"));
const CategoryPage = lazy(() => import("./archive/CategoryPage"));
const BornPage = lazy(() => import("./archive/BornPage"));
const MethodsPage = lazy(() => import("./archive/MethodsPage"));
const SeasonPage = lazy(() => import("./season/SeasonPage"));

function NotFound() {
  usePageTitle("Wrong envelope");
  return (
    <ArchivePage title="Wrong envelope">
      <PageHead title="Wrong envelope">
        <p>
          This page isn’t on the programme. <Link to="/">Return to the show</Link>.
        </p>
      </PageHead>
    </ArchivePage>
  );
}

/** Each new page starts at its top, while anchors within the show are left to the browser. */
function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (!hash) window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname, hash]);
  return null;
}

export function App() {
  return (
    <SearchProvider>
      <ScrollToTop />
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Suspense fallback={<div className="page-loading" />}>
        <Routes>
          <Route path="/" element={<TheShow />} />
          <Route path="/ceremonies" element={<CeremoniesPage />} />
          <Route path="/ceremonies/:number" element={<CeremonyPage />} />
          <Route path="/films/:id" element={<FilmPage />} />
          <Route path="/people/:id" element={<PersonPage />} />
          <Route path="/studios/:id" element={<PersonPage />} />
          <Route path="/categories" element={<CategoriesPage />} />
          <Route path="/categories/:slug" element={<CategoryPage />} />
          <Route path="/born/:year" element={<BornPage />} />
          <Route path="/methods" element={<MethodsPage />} />
          <Route path="/season" element={<SeasonPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </SearchProvider>
  );
}
