import React from "react";
import ReactDOM from "react-dom/client";

import ESSAIWidget from "./components/ESSAIWidget";

import "./index.css";
import "./styles/Sidebar.css";
import "./styles/ChatBox.css";
import "./styles/Header.css";


function startESSAI() {

  let rootElement =
    document.getElementById("ess-ai-root");


  // If the official website doesn't provide
  // the container, create it automatically.

  if (!rootElement) {

    rootElement =
      document.createElement("div");

    rootElement.id = "ess-ai-root";

    document.body.appendChild(rootElement);

  }


  ReactDOM.createRoot(rootElement).render(

    <React.StrictMode>

      <ESSAIWidget />

    </React.StrictMode>

  );

}


// Wait until the page is ready

if (document.readyState === "loading") {

  document.addEventListener(
    "DOMContentLoaded",
    startESSAI
  );

} else {

  startESSAI();

}