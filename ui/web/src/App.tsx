import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { OverviewPage } from "@/pages/Overview";
import { GraphPage } from "@/pages/Graph";
import { AgentsPage } from "@/pages/Agents";
import { ActivityPage } from "@/pages/Activity";
import { PipelinePage } from "@/pages/Pipeline";
import { RunsPage } from "@/pages/Runs";
import { InboxPage } from "@/pages/Inbox";
import { NewProjectPage } from "@/pages/NewProject";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "new", element: <NewProjectPage /> },
      { path: "pipeline", element: <PipelinePage /> },
      { path: "inbox", element: <InboxPage /> },
      { path: "runs", element: <RunsPage /> },
      { path: "activity", element: <ActivityPage /> },
      { path: "agents", element: <AgentsPage /> },
      { path: "graph", element: <GraphPage /> },
      { path: "memory", element: <Navigate to="/graph" replace /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);

export function App(): React.ReactElement {
  return <RouterProvider router={router} />;
}
