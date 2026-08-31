import { useState, useEffect } from "react";

import ChatBox from "../components/ChatBox";
import Sidebar from "../components/Sidebar";

import api from "../services/api";
import { getToken } from "../services/token";
import { logoutUser } from "../services/auth";


function AIMode({ embedded = false }) {

  const [messages, setMessages] = useState([]);

  const [history, setHistory] = useState([]);


  // =====================================================
  // LOAD CHAT HISTORY
  // =====================================================

  async function loadHistory() {

    const token = getToken();

    // Guest users have no history
    if (!token) {

      setHistory([]);

      return;

    }


    try {

      const response = await api.get(
        "/chat/history",
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );


      console.log(
        "History loaded:",
        response.data
      );


      setHistory(response.data);


    } catch (error) {

      console.log(
        "History loading error:",
        error.response?.data || error.message
      );

    }

  }


  // =====================================================
  // LOAD HISTORY WHEN AI MODE OPENS
  // =====================================================

  useEffect(() => {

    loadHistory();

  }, []);


  // =====================================================
  // NEW CHAT
  // =====================================================

  function newChat() {

    setMessages([]);

  }


  // =====================================================
  // OPEN CHAT HISTORY
  // =====================================================

  function openHistory(chat) {

    setMessages([

      {
        role: "user",
        text: chat.message
      },

      {
        role: "bot",
        text: chat.response
      }

    ]);

  }


  // =====================================================
  // LOGOUT
  // =====================================================

  function handleLogout() {

    logoutUser();

    setMessages([]);

    setHistory([]);

    window.location.href = "/";

  }


  // =====================================================
  // ESS AI MODE
  // =====================================================

  return (

    <div
      className={
        embedded
          ? "app-layout embedded-ai-layout"
          : "app-layout"
      }
    >


      {/* =================================================
          EXISTING SIDEBAR
      ================================================= */}

      <Sidebar

        history={history}

        newChat={newChat}

        openHistory={openHistory}

        logout={handleLogout}

      />


      {/* =================================================
          EXISTING MAIN CHAT
      ================================================= */}

      <main className="main">

        <ChatBox

          messages={messages}

          setMessages={setMessages}

          loadHistory={loadHistory}

          embedded={embedded}

        />

      </main>


    </div>

  );

}


export default AIMode;