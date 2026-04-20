import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { OverviewPage } from "@/pages/Overview";
import { MemoryPage } from "@/pages/Memory";
import { GraphPage } from "@/pages/Graph";
import { ActivityPage } from "@/pages/Activity";
import { PipelinePage } from "@/pages/Pipeline";
import { SessionsPage } from "@/pages/Sessions";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "pipeline", element: <PipelinePage /> },
      { path: "activity", element: <ActivityPage /> },
      { path: "graph", element: <GraphPage /> },
      { path: "memory", element: <MemoryPage /> },
      { path: "sessions", element: <SessionsPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);

export function App(): React.ReactElement {
  return <RouterProvider router={router} />;
}
