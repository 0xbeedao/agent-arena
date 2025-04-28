import { createRouter } from "@tanstack/react-router";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import { routeTree } from "./routeTree.gen.ts";
import "./styles/tailwind.css";

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
		</React.StrictMode>
	);
}
