import React from "react";
import { createRoot } from "react-dom/client";

import "../index.css";
import "../styles/App.css";
import "../styles/ChatBox.css";
import "../components/ESSAIWidget.css";

import ESSAIWidget from "../components/ESSAIWidget";

const container = document.getElementById("ess-ai-widget");

if (container) {
  const root = createRoot(container);

  root.render(
    <React.StrictMode>
      <ESSAIWidget />
    </React.StrictMode>
  );
}