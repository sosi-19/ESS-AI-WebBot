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

    // New file has not been uploaded yet.
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

            if (typeof errorData.detail === "string") {

              errorMessage =
                errorData.detail;

            } else {

              errorMessage =
                JSON.stringify(
                  errorData.detail
                );

            }

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

    // -------------------------------------------------
    // Empty message
    // -------------------------------------------------

    if (!input.trim()) {
      return;
    }

    // -------------------------------------------------
    // Prevent duplicate requests
    // -------------------------------------------------

    if (loading) {
      return;
    }


    // -------------------------------------------------
    // Selected PDF must be uploaded first
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
    // IMPORTANT:
    // Save current file ID before state changes
    // -------------------------------------------------

    const currentFileId =
      fileId;


    // -------------------------------------------------
    // Authentication
    // -------------------------------------------------

    const token =
      localStorage.getItem("token");


    const isAuthenticated =
      Boolean(token);


    // -------------------------------------------------
    // Choose endpoint
    // -------------------------------------------------

    const chatEndpoint =
      isAuthenticated
        ? `${API_BASE_URL}/chat/stream`
        : `${API_BASE_URL}/chat/public/stream`;


    // =================================================
    // DEBUG
    // =================================================

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
      selectedFile?.name || "None"
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


    // -------------------------------------------------
    // Clear input
    // -------------------------------------------------

    setInput("");

    setLoading(true);


    try {

      // =================================================
      // REQUEST BODY
      // =================================================

      const requestBody = {

        message:
          userText,

        file_id:
          currentFileId || null,

      };


      console.log(
        "📦 REQUEST BODY:",
        requestBody
      );


      // =================================================
      // SEND REQUEST
      // =================================================

      const response = await fetch(

        chatEndpoint,

        {

          method: "POST",

          headers: {

            "Content-Type":
              "application/json",

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


      // =================================================
      // HTTP ERROR
      // =================================================

      if (!response.ok) {

        let errorMessage =
          `HTTP error: ${response.status}`;


        try {

          const errorData =
            await response.json();


          if (errorData.detail) {

            if (
              typeof errorData.detail ===
              "string"
            ) {

              errorMessage =
                errorData.detail;

            } else {

              errorMessage =
                JSON.stringify(
                  errorData.detail
                );

            }

          }

        } catch {
          // Ignore JSON parsing error
        }


        // -------------------------------------------------
        // Authentication error
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


      // =================================================
      // STREAMING CHECK
      // =================================================

      if (!response.body) {

        throw new Error(
          "Streaming is not supported by this response."
        );

      }


      // =================================================
      // CREATE BOT MESSAGE
      // =================================================

      setMessages((prev) => [

        ...prev,

        {
          role: "bot",
          text: "",
          sources: [],
        },

      ]);


      // =================================================
      // STREAM READER
      // =================================================

      const reader =
        response.body.getReader();


      const decoder =
        new TextDecoder("utf-8");


      let buffer = "";
      let fullAnswer = "";
      let streamFinished = false;


      // =================================================
      // UPDATE BOT MESSAGE
      // =================================================

      function updateBotMessage(answer) {

        setMessages((prev) => {

          if (!prev.length) {
            return prev;
          }


          const updated = [
            ...prev,
          ];


          const lastIndex =
            updated.length - 1;


          // Make sure we update the bot message,
          // not the user's message.

          if (
            updated[lastIndex].role !==
            "bot"
          ) {

            updated.push({
              role: "bot",
              text: answer,
              sources: [],
            });

            return updated;

          }


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

      function updateBotSources(sources) {

        setMessages((prev) => {

          if (!prev.length) {
            return prev;
          }


          const updated = [
            ...prev,
          ];


          const lastIndex =
            updated.length - 1;


          if (
            updated[lastIndex].role !==
            "bot"
          ) {

            return updated;

          }


          updated[lastIndex] = {

            ...updated[lastIndex],

            sources:
              sources,

          };


          return updated;

        });

      }


      // =================================================
      // PROCESS ONE NDJSON LINE
      // =================================================

      function processLine(line) {

        const cleanLine =
          line.trim();


        if (!cleanLine) {
          return;
        }


        try {

          const data =
            JSON.parse(cleanLine);


          console.log(
            "🌊 Stream data:",
            data
          );


          // =================================================
          // STREAMED RESPONSE TEXT
          // =================================================

          if (
            typeof data.response ===
            "string"
          ) {

            fullAnswer +=
              data.response;


            updateBotMessage(
              fullAnswer
            );


            console.log(
              "📝 Current answer:",
              fullAnswer
            );

          }


          // =================================================
          // SOURCES
          // =================================================

          if (
            Array.isArray(
              data.sources
            )
          ) {

            updateBotSources(
              data.sources
            );

          }


          // =================================================
          // BACKEND ERROR
          // =================================================

          if (data.error) {

            console.error(
              "❌ Backend stream error:",
              data.error
            );


            if (!fullAnswer.trim()) {

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


          // =================================================
          // STREAM FINISHED
          // =================================================

          if (data.done === true) {

            streamFinished = true;


            console.log(
              "================================================"
            );

            console.log(
              "🌊 STREAM FINISHED"
            );

            console.log(
              "Final answer:",
              fullAnswer
            );

            console.log(
              "Answer length:",
              fullAnswer.length
            );

            console.log(
              "================================================"
            );

          }

        } catch (error) {

          console.warn(
            "⚠️ Could not parse streaming line:",
            cleanLine
          );

          console.warn(
            "Parser error:",
            error
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


        // -------------------------------------------------
        // Stream connection closed
        // -------------------------------------------------

        if (done) {
          break;
        }


        // -------------------------------------------------
        // Decode bytes
        // -------------------------------------------------

        buffer +=
          decoder.decode(
            value,
            {
              stream: true,
            }
          );


        // -------------------------------------------------
        // Split NDJSON lines
        // -------------------------------------------------

        const lines =
          buffer.split("\n");


        // -------------------------------------------------
        // Keep incomplete line
        // -------------------------------------------------

        buffer =
          lines.pop() || "";


        // -------------------------------------------------
        // Process complete lines
        // -------------------------------------------------

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
      // PROCESS LAST LINE
      // =================================================

      if (buffer.trim()) {

        processLine(
          buffer
        );

      }


      // =================================================
      // EMPTY RESPONSE FALLBACK
      // =================================================

      if (!fullAnswer.trim()) {

        fullAnswer =
          "The AI did not return a response.";


        updateBotMessage(
          fullAnswer
        );

      }


      // =================================================
      // FINAL DEBUG
      // =================================================

      console.log(
        "================================================"
      );

      console.log(
        "✅ COMPLETE ANSWER RECEIVED"
      );

      console.log(
        "Answer:",
        fullAnswer
      );

      console.log(
        "Total answer characters:",
        fullAnswer.length
      );

      console.log(
        "Stream finished:",
        streamFinished
      );

      console.log(
        "File ID:",
        currentFileId
      );

      console.log(
        "Authenticated:",
        isAuthenticated
      );

      console.log(
        "================================================"
      );


      // =================================================
      // RELOAD HISTORY
      // =================================================
      //
      // Only authenticated users have saved history.
      //
      // Guest users do NOT reload history.
      //
      // =================================================

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


      // =================================================
      // SHOW ERROR IN BOT MESSAGE
      // =================================================

      setMessages((prev) => {

        const updated = [
          ...prev,
        ];


        const lastIndex =
          updated.length - 1;


        const errorText =
          `❌ ${
            error.message ||
            "Sorry, something went wrong. Please try again."
          }`;


        // -------------------------------------------------
        // Existing bot message
        // -------------------------------------------------

        if (
          lastIndex >= 0 &&
          updated[lastIndex].role ===
            "bot"
        ) {

          updated[lastIndex] = {

            ...updated[lastIndex],

            text:
              errorText,

          };


          return updated;

        }


        // -------------------------------------------------
        // No bot message
        // -------------------------------------------------

        updated.push({

          role: "bot",

          text:
            errorText,

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


        {/* ----------------------------------------- */}
        {/* THINKING INDICATOR */}
        {/* ----------------------------------------- */}

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
          {/* FILE NOT UPLOADED */}
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
          {/* UPLOADING */}
          {/* ----------------------------------- */}

          {uploading && (

            <span>

              ⏳ Uploading...

            </span>

          )}


          {/* ----------------------------------- */}
          {/* UPLOADED */}
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
        {/* HIDDEN FILE INPUT */}
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
        {/* UPLOAD BUTTON */}
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
        {/* TEXT INPUT */}
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
        {/* SEND BUTTON */}
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