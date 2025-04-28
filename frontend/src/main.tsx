import { createRouter } from "@tanstack/react-router";
import { QueryClient } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createSyncStoragePersister } from "@tanstack/query-sync-storage-persister";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import { routeTree } from "./routeTree.gen.ts";
import "./styles/tailwind.css";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 1000 * 60 * 60 * 24, // 24 hours
    },
  },
});

// Create a persister
const persister = createSyncStoragePersister({
  storage: window.localStorage,
});

// Create the router
const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
	interface Register {
		// This infers the type of our router and registers it across your entire project
		router: typeof router;
	}
}

const rootElement = document.querySelector("#root") as Element;
if (!rootElement.innerHTML) {
	const root = ReactDOM.createRoot(rootElement);
	root.render(
		<React.StrictMode>
			<PersistQueryClientProvider
				client={queryClient}
				persistOptions={{ persister }}
			>
				<React.Suspense fallback="loading">
					<title>Artful One</title>
					<link href="/images/favicons/favicon.ico" rel="icon" type="image/x-icon" />
					<link href="/images/favicons/favicon.ico" rel="shortcut icon" type="image/x-icon" />
					<link href="/images/favicons/favicon-180x180.png" rel="apple-touch-icon" sizes="180x180" />
					<link href="/images/favicons/favicon-192x192.png" rel="icon" sizes="192x192" type="image/png" />
					<link href="https://arena.misteragent.dev" rel="canonical" />
					<link href="https://fonts.googleapis.com" rel="preconnect" />
					<link crossOrigin="anonymous" href="https://fonts.gstatic.com" rel="preconnect" />
					<link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@200..900&family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Merriweather:ital,opsz,wght@0,18..144,300..900;1,18..144,300..900&display=swap" rel="stylesheet" />
					<meta content="follow,index" name="robots" />
					<App router={router} />
				</React.Suspense>
				<ReactQueryDevtools initialIsOpen={false} />
			</PersistQueryClientProvider>
		</React.StrictMode>
	);
}
