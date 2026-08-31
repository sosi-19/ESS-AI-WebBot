import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AIMode from "../pages/AIMode";
import "./ESSAIWidget.css";

function ESSAIWidget() {

  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [maximized, setMaximized] = useState(false);

  const navigate = useNavigate();

  const token = localStorage.getItem("token");

  // =====================================================
  // OPEN
  // =====================================================

  function openAI() {
    setOpen(true);
    setMinimized(false);
  }

  // =====================================================
  // CLOSE
  // =====================================================

  function closeAI() {
    setOpen(false);
    setMinimized(false);
    setMaximized(false);
  }

  // =====================================================
  // MINIMIZE
  // =====================================================

  function minimizeAI() {
    setMinimized((prev) => !prev);
  }

  // =====================================================
  // MAXIMIZE
  // =====================================================

  function maximizeAI() {
    setMaximized((prev) => !prev);
    setMinimized(false);
  }

  // =====================================================
  // LOGIN
  // =====================================================

  function goLogin() {
    closeAI();
    navigate("/login");
  }

  // =====================================================
  // REGISTER
  // =====================================================

  function goRegister() {
    closeAI();
    navigate("/register");
  }

  // =====================================================
  // RENDER
  // =====================================================

  return (
    <>
      {/* =================================================
          FLOATING ESS AI BUTTON
      ================================================= */}

      {!open && (
        <button
          className="ess-ai-launcher"
          onClick={openAI}
        >
          <span className="ess-ai-icon">
            🤖
          </span>

          <span>
            ESS AI
          </span>
        </button>
      )}


      {/* =================================================
          ESS AI POPUP
      ================================================= */}

      {open && (
        <div className="ess-ai-overlay">

          {/* BACKDROP */}

          <div
            className="ess-ai-backdrop"
            onClick={closeAI}
          />


          {/* =================================================
              POPUP WINDOW
          ================================================= */}

          <div
            className={`ess-ai-window
              ${minimized ? "is-minimized" : ""}
              ${maximized ? "is-maximized" : ""}
            `}
          >

            {/* =================================================
                POPUP HEADER
            ================================================= */}

            <div className="ess-ai-window-header">

              {/* LEFT */}

              <div className="ess-ai-title">

                <span className="ess-ai-title-icon">
                  🤖
                </span>

                <div className="ess-ai-title-text">

                  <strong>
                    ESS AI
                  </strong>

                  <small>
                    Ethiopia Statistical Service
                  </small>

                </div>

              </div>


              {/* =================================================
                  RIGHT ACTIONS
              ================================================= */}

              <div className="ess-ai-actions">

                {/* GUEST */}

                {!token && (
                  <button
                    className="ess-ai-auth guest"
                    onClick={() => {
                      closeAI();
                      navigate("/");
                    }}
                  >
                    Guest
                  </button>
                )}


                {/* LOGIN */}

                {!token && (
                  <button
                    className="ess-ai-auth login"
                    onClick={goLogin}
                  >
                    Login
                  </button>
                )}


                {/* REGISTER */}

                {!token && (
                  <button
                    className="ess-ai-auth register"
                    onClick={goRegister}
                  >
                    Register
                  </button>
                )}


                {/* MINIMIZE */}

                <button
                  className="ess-ai-control"
                  onClick={minimizeAI}
                  title="Minimize"
                >
                  −
                </button>


                {/* MAXIMIZE */}

                <button
                  className="ess-ai-control"
                  onClick={maximizeAI}
                  title="Maximize"
                >
                  ⛶
                </button>


                {/* CLOSE */}

                <button
                  className="ess-ai-close"
                  onClick={closeAI}
                  title="Close"
                >
                  ✕
                </button>

              </div>

            </div>


            {/* =================================================
                EXISTING AIMODE
                SIDEBAR + CHATBOX
            ================================================= */}

            {!minimized && (
              <div className="ess-ai-content">

                <AIMode />

              </div>
            )}

          </div>

        </div>
      )}
    </>
  );
}

export default ESSAIWidget;