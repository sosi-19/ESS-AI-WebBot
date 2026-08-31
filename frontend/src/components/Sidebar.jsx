function Sidebar({ history, newChat, openHistory, logout }) {

  return (
    <div className="sidebar">

      <h2>🤖 ESS AI</h2>


      <button 
        className="new-chat"
        onClick={newChat}
      >
        ➕ New Chat
      </button>


      <h3 className="recent-title">
        🕘 Recent Chats
      </h3>


      <div className="history">

        {history.length === 0 ? (

          <p className="empty">
            No previous chats
          </p>

        ) : (

          history.map((chat)=>(

            <div
              key={chat.id}
              className="chat-item"
              onClick={() => openHistory(chat)}
            >
              💬 {chat.message.slice(0,30)}
            </div>

          ))

        )}

      </div>


      <div className="topics">

        <div>📊 Population Questions</div>

        <div>🌾 Agriculture Data</div>

        <div>💰 Economy & GDP</div>

        <div>🏠 Housing Census</div>

      </div>


      <div className="sidebar-bottom">

        {logout && (
          <button onClick={logout}>
            🚪 Logout
          </button>
        )}

      </div>


    </div>
  );
}


export default Sidebar;