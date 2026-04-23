import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { Dashboard } from "./screens/Dashboard";
import { OpenIPOs } from "./screens/OpenIPOs";
import { UpcomingIPOs } from "./screens/UpcomingIPOs";
import { PastPredictions } from "./screens/PastPredictions";
import { Watchlist } from "./screens/Watchlist";
import { Analytics } from "./screens/Analytics";
import { IPODetail } from "./screens/IPODetail";
import { Settings } from "./screens/Settings";
import { NotFound } from "./screens/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "open", Component: OpenIPOs },
      { path: "upcoming", Component: UpcomingIPOs },
      { path: "past", Component: PastPredictions },
      { path: "watchlist", Component: Watchlist },
      { path: "analytics", Component: Analytics },
      { path: "ipo/:slug", Component: IPODetail },
      { path: "settings", Component: Settings },
      { path: "*", Component: NotFound },
    ],
  },
]);
