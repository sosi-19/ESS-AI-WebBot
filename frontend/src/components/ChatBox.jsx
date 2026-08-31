import API_BASE_URL from "../config";

import { useState, useRef, useEffect } from "react";

import Message from "./Message";
import Header from "./Header";

import "../styles/ChatBox.css";


function ChatBox({ messages, setMessages, loadHistory }) {

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // =====================================================
  // UPLOAD STATES
  // =====================================================

  const [selectedFile, setSelectedFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);


  // =====================================================
  // AUTO SCROLL
  // =====================================================

  useEffect(() => {

    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [messages, loading]);


  // =====================================================
  // SELECT PDF
  // =====================================================

  function handleFileSelect(event) {

    const file = event.target.files?.[0];

    if (!file) {
      return;
    }


    // -------------------------------------------------
    // Only PDF files
    // -------------------------------------------------

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {

      setUploadMessage(
        "❌ Please select a PDF file."
      );

      setSelectedFile(null);
      setFileId(null);

      return;
    }


    // -------------------------------------------------
    // Save selected file
    // -------------------------------------------------

    setSelectedFile(file);

    // New file must be uploaded first.
    setFileId(null);

    setUploadMessage("");

    console.log(
      "📄 Selected PDF:",
      file.name
    );

  }


  // =====================================================
  // UPLOAD PDF
  // =====================================================

  async function uploadFile() {

    if (!selectedFile) {

      setUploadMessage(
        "❌ Please select a PDF first."
      );

      return;
    }


    if (uploading) {
      return;
    }


    setUploading(true);
    setUploadMessage("");


    try {

      const token =
        localStorage.getItem("token");


      // -------------------------------------------------
      // Create FormData
      // -------------------------------------------------

      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );


      console.log(
        "================================================"
      );

      console.log(
        "📤 UPLOAD REQUEST"
      );

      console.log(
        "📄 File:",
        selectedFile.name
      );

      console.log(
        "🌐 API:",
        `${API_BASE_URL}/upload/`
      );

      console.log(
        "🔐 Authenticated:",
        Boolean(token)
      );

      console.log(
        "================================================"
      );


      // -------------------------------------------------
      // Upload request
      // -------------------------------------------------

      const response = await fetch(

        `${API_BASE_URL}/upload/`,

        {

          method: "POST",

          headers: {

            ...(token
              ? {
                  Authorization:
                    `Bearer ${token}`,
                }
              : {}),

          },

          body: formData,

        }

      );


      // -------------------------------------------------
      // HTTP error
      // -------------------------------------------------

      if (!response.ok) {

        let errorMessage =
          `Upload failed: ${response.status}`;

        try {

          const errorData =
            await response.json();

          if (errorData.detail) {

            errorMessage =
              errorData.detail;

          }

        } catch {
          // Ignore JSON parsing error
        }

        throw new Error(
          errorMessage
        );

      }


      // -------------------------------------------------
      // Read response
      // -------------------------------------------------

      const data =
        await response.json();


      console.log(
        "📤 Upload response:",
        data
      );


      // -------------------------------------------------
      // Backend MUST return file_id
      // -------------------------------------------------

      if (!data.file_id) {

        throw new Error(
          "Backend did not return file_id."
        );

      }


      // -------------------------------------------------
      // Save file ID
      // -------------------------------------------------

      setFileId(
        data.file_id
      );


      const filename =
        data.filename ||
        selectedFile.name;


      console.log(
        "================================================"
      );

      console.log(
        "✅ PDF UPLOAD SUCCESSFUL"
      );

      console.log(
        "📄 File:",
        filename
      );

      console.log(
        "📎 FILE ID:",
        data.file_id
      );

      console.log(
        "================================================"
      );


      setUploadMessage(
        `✅ ${filename} uploaded successfully.`
      );


    } catch (error) {

      console.error(
        "❌ Upload error:",
        error
      );


      setFileId(null);


      setUploadMessage(
        `❌ ${
          error.message ||
          "File upload failed. Please try again."
        }`
      );


    } finally {

      setUploading(false);

    }

  }


  // =====================================================
  // SEND MESSAGE
  // =====================================================

  async function sendMessage() {

    if (!input.trim()) {
      return;
    }


    if (loading) {
      return;
    }


    // -------------------------------------------------
    // If a PDF is selected but not uploaded
    // -------------------------------------------------

    if (selectedFile && !fileId) {

      setUploadMessage(
        "⚠️ Please upload the PDF before asking a question about it."
      );

      return;

    }


    const userText =
      input.trim();


    // -------------------------------------------------
    // Save file ID before anything changes
    // -------------------------------------------------

    const currentFileId =
      fileId;


    // -------------------------------------------------
    // Get authentication token
    // -------------------------------------------------

    const token =
      localStorage.getItem("token");


    // =================================================
    // IMPORTANT
    // =================================================
    //
    // Logged-in user:
    //
    //     /chat/stream
    //
    // Guest:
    //
    //     /chat/public/stream
    //
    // =================================================

    const chatEndpoint =
      token
        ? `${API_BASE_URL}/chat/stream`
        : `${API_BASE_URL}/chat/public/stream`;


    const isAuthenticated =
      Boolean(token);


    // -------------------------------------------------
    // Debug
    // -------------------------------------------------

    console.log(
      "================================================"
    );

    console.log(
      "💬 CHAT REQUEST"
    );

    console.log(
      "Question:",
      userText
    );

    console.log(
      "📎 Selected file:",
      selectedFile?.name ||
        "None"
    );

    console.log(
      "📎 FILE ID BEING SENT:",
      currentFileId
    );

    console.log(
      "🔐 Authenticated:",
      isAuthenticated
    );

    console.log(
      "🌐 CHAT ENDPOINT:",
      chatEndpoint
    );

    console.log(
      "================================================"
    );


    // -------------------------------------------------
    // Add user message
    // -------------------------------------------------

    setMessages((prev) => [

      ...prev,

      {
        role: "user",
        text: userText,
      },

    ]);


    setInput("");
    setLoading(true);


    try {


      // -------------------------------------------------
      // Request body
      // -------------------------------------------------

      const requestBody = {

        message:
          userText,

        file_id:
          currentFileId,

      };


      console.log(
        "📦 REQUEST BODY:",
        requestBody
      );


      // -------------------------------------------------
      // Streaming request
      // -------------------------------------------------

      const response = await fetch(

        chatEndpoint,

        {

          method: "POST",

          headers: {

            "Content-Type":
              "application/json",

            // Only send Authorization
            // when the user is logged in.

            ...(token
              ? {
                  Authorization:
                    `Bearer ${token}`,
                }
              : {}),

          },

          body: JSON.stringify(
            requestBody
          ),

        }

      );


      // -------------------------------------------------
      // HTTP error
      // -------------------------------------------------

      if (!response.ok) {

        let errorMessage =
          `HTTP error: ${response.status}`;


        try {

          const errorData =
            await response.json();

          if (errorData.detail) {

            errorMessage =
              errorData.detail;

          }

        } catch {
          // Ignore JSON parsing error
        }


        // -------------------------------------------------
        // Token may have expired
        // -------------------------------------------------

        if (
          response.status === 401 &&
          token
        ) {

          console.warn(
            "⚠️ Authentication token is invalid or expired."
          );

        }


        throw new Error(
          errorMessage
        );

      }


      // -------------------------------------------------
      // Make sure streaming exists
      // -------------------------------------------------

      if (!response.body) {

        throw new Error(
          "Streaming is not supported by this response."
        );

      }


      // -------------------------------------------------
      // Create empty bot message
      // -------------------------------------------------

      setMessages((prev) => [

        ...prev,

        {
          role: "bot",
          text: "",
          sources: [],
        },

      ]);


      // -------------------------------------------------
      // Stream reader
      // -------------------------------------------------

      const reader =
        response.body.getReader();


      const decoder =
        new TextDecoder();


      let buffer = "";
      let fullAnswer = "";


      // =================================================
      // UPDATE BOT MESSAGE
      // =================================================

      function updateBotMessage(
        answer
      ) {

        setMessages((prev) => {

          if (!prev.length) {
            return prev;
          }


          const updated = [
            ...prev,
          ];


          const lastIndex =
            updated.length - 1;


          updated[lastIndex] = {

            ...updated[lastIndex],

            text:
              answer,

          };


          return updated;

        });

      }


      // =================================================
      // UPDATE BOT SOURCES
      // =================================================

      function updateBotSources(
        sources
      ) {

        setMessages((prev) => {

          if (!prev.length) {
            return prev;
          }


          const updated = [
            ...prev,
          ];


          const lastIndex =
            updated.length - 1;


          updated[lastIndex] = {

            ...updated[lastIndex],

            sources:
              sources,

          };


          return updated;

        });

      }


      // =================================================
      // PROCESS ONE JSON LINE
      // =================================================

      function processLine(line) {

        if (!line.trim()) {
          return;
        }


        try {

          const data =
            JSON.parse(line);


          console.log(
            "🌊 Stream data:",
            data
          );


          // ------------------------------------------------
          // Normal streaming response
          // ------------------------------------------------

          if (
            typeof data.response ===
            "string"
          ) {

            fullAnswer +=
              data.response;


            updateBotMessage(
              fullAnswer
            );

          }


          // ------------------------------------------------
          // Sources
          // ------------------------------------------------

          if (
            data.sources &&
            Array.isArray(
              data.sources
            )
          ) {

            updateBotSources(
              data.sources
            );

          }


          // ------------------------------------------------
          // Backend error
          // ------------------------------------------------

          if (data.error) {

            console.error(
              "❌ Backend stream error:",
              data.error
            );


            if (!fullAnswer) {

              fullAnswer =
                `❌ ${data.error}`;

            } else {

              fullAnswer +=
                `\n❌ ${data.error}`;

            }


            updateBotMessage(
              fullAnswer
            );

          }


          // ------------------------------------------------
          // Stream finished
          // ------------------------------------------------

          if (data.done) {

            console.log(
              "🌊 Stream finished"
            );

          }


        } catch (error) {

          console.warn(
            "⚠️ Could not parse streaming line:",
            line
          );

        }

      }


      // =================================================
      // READ STREAM
      // =================================================

      while (true) {

        const {
          value,
          done,
        } = await reader.read();


        if (done) {
          break;
        }


        buffer +=
          decoder.decode(
            value,
            {
              stream: true,
            }
          );


        const lines =
          buffer.split("\n");


        // Keep incomplete line

        buffer =
          lines.pop() || "";


        for (
          const line of lines
        ) {

          processLine(line);

        }

      }


      // =================================================
      // FLUSH DECODER
      // =================================================

      buffer +=
        decoder.decode();


      // =================================================
      // PROCESS REMAINING BUFFER
      // =================================================

      if (buffer.trim()) {

        processLine(
          buffer
        );

      }


      // =================================================
      // STREAM COMPLETE
      // =================================================

      console.log(
        "================================================"
      );

      console.log(
        "✅ COMPLETE ANSWER RECEIVED"
      );

      console.log(
        "Total answer characters:",
        fullAnswer.length
      );

      console.log(
        "Authenticated:",
        isAuthenticated
      );

      console.log(
        "================================================"
      );


      // -------------------------------------------------
      // Reload history ONLY for logged-in users
      // -------------------------------------------------

      if (
        isAuthenticated &&
        loadHistory
      ) {

        console.log(
          "🕘 Reloading authenticated chat history..."
        );


        try {

          await loadHistory();


          console.log(
            "✅ Chat history reloaded"
          );

        } catch (historyError) {

          console.error(
            "❌ Failed to reload chat history:",
            historyError
          );

        }

      }


    } catch (error) {

      console.error(
        "❌ Streaming error:",
        error
      );


      // -------------------------------------------------
      // Put error into existing bot message
      // -------------------------------------------------

      setMessages((prev) => {

        const updated = [
          ...prev,
        ];


        const lastIndex =
          updated.length - 1;


        if (
          lastIndex >= 0 &&
          updated[lastIndex].role === "bot"
        ) {

          updated[lastIndex] = {

            ...updated[lastIndex],

            text:
              `❌ ${
                error.message ||
                "Sorry, something went wrong. Please try again."
              }`,

          };


          return updated;

        }


        // -------------------------------------------------
        // If no bot message exists
        // -------------------------------------------------

        updated.push({

          role: "bot",

          text:
            `❌ ${
              error.message ||
              "Sorry, something went wrong. Please try again."
            }`,

          sources: [],

        });


        return updated;

      });


    } finally {

      setLoading(false);

    }

  }


  // =====================================================
  // CLEAR UPLOADED FILE
  // =====================================================

  function clearFile() {

    console.log(
      "🗑️ Clearing uploaded file"
    );


    setSelectedFile(null);
    setFileId(null);
    setUploadMessage("");


    if (
      fileInputRef.current
    ) {

      fileInputRef.current.value =
        "";

    }

  }


  // =====================================================
  // RENDER
  // =====================================================

  return (

    <div className="chat-container">


      <Header />


      {/* ========================================= */}
      {/* MESSAGES */}
      {/* ========================================= */}

      <div className="messages">

        {messages.map(
          (msg, index) => (

            <Message
              key={index}
              role={msg.role}
              text={msg.text}
              sources={msg.sources}
            />

          )
        )}


        {loading && (

          <div className="message bot">

            ⏳ Thinking...

          </div>

        )}


        <div
          ref={bottomRef}
        />

      </div>


      {/* ========================================= */}
      {/* UPLOAD PREVIEW */}
      {/* ========================================= */}

      {selectedFile && (

        <div className="upload-preview">


          <span>

            📄{" "}

            {selectedFile.name}

          </span>


          {/* ----------------------------------- */}
          {/* File selected but not uploaded */}
          {/* ----------------------------------- */}

          {!fileId &&
            !uploading && (

              <button
                type="button"
                onClick={
                  uploadFile
                }
              >

                Upload

              </button>

            )}


          {/* ----------------------------------- */}
          {/* Uploading */}
          {/* ----------------------------------- */}

          {uploading && (

            <span>

              ⏳ Uploading...

            </span>

          )}


          {/* ----------------------------------- */}
          {/* Successfully uploaded */}
          {/* ----------------------------------- */}

          {fileId && (

            <>

              <span>

                ✅ Uploaded

              </span>


              <button
                type="button"
                onClick={
                  clearFile
                }
              >

                ✕

              </button>

            </>

          )}

        </div>

      )}


      {/* ========================================= */}
      {/* UPLOAD MESSAGE */}
      {/* ========================================= */}

      {uploadMessage && (

        <div className="upload-message">

          {uploadMessage}

        </div>

      )}


      {/* ========================================= */}
      {/* INPUT AREA */}
      {/* ========================================= */}

      <div className="input-area">


        {/* --------------------------------------- */}
        {/* Hidden PDF input */}
        {/* --------------------------------------- */}

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={
            handleFileSelect
          }
          style={{
            display: "none",
          }}
        />


        {/* --------------------------------------- */}
        {/* Upload button */}
        {/* --------------------------------------- */}

        <button
          type="button"
          className="upload-btn"
          onClick={() =>
            fileInputRef.current?.click()
          }
          disabled={
            loading ||
            uploading
          }
        >

          📎

        </button>


        {/* --------------------------------------- */}
        {/* Text input */}
        {/* --------------------------------------- */}

        <input
          value={input}
          onChange={(e) =>
            setInput(
              e.target.value
            )
          }
          placeholder="💬 Ask ESS AI Assistant..."
          disabled={loading}
          onKeyDown={(e) => {

            if (
              e.key === "Enter" &&
              !e.shiftKey
            ) {

              e.preventDefault();

              sendMessage();

            }

          }}
        />


        {/* --------------------------------------- */}
        {/* Send button */}
        {/* --------------------------------------- */}

        <button
          type="button"
          onClick={
            sendMessage
          }
          disabled={
            loading ||
            uploading ||
            !input.trim()
          }
        >

          {loading
            ? "⏳"
            : "Send ➤"}

        </button>


      </div>

    </div>

  );

}


export default ChatBox;