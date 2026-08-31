import "../styles/Header.css";


function Header() {

  const token = localStorage.getItem("token");


  // =====================================================
  // LOGOUT
  // =====================================================

  function handleLogout() {

    localStorage.removeItem("token");

    window.location.href = "/login";

  }


  // =====================================================
  // LOGIN
  // =====================================================

  function handleLogin() {

    window.location.href = "/login";

  }


  // =====================================================
  // REGISTER
  // =====================================================

  function handleRegister() {

    window.location.href = "/register";

  }


  // =====================================================
  // RENDER
  // =====================================================

  return (

    <div className="header">


      {/* =================================================
          HEADER TITLE
      ================================================= */}

      <div>

        <h2>
          🤖 ESS AI Assistant
        </h2>

        <p>
          Ethiopia Statistical Service
        </p>

      </div>


      {/* =================================================
          HEADER RIGHT
      ================================================= */}

      <div className="header-right">


        {/* ===============================================
            ONLINE STATUS
        =============================================== */}

        <span className="online">
          🟢 Online
        </span>


        {/* ===============================================
            AUTHENTICATED USER
        =============================================== */}

        {token ? (

          <button
            type="button"
            className="auth-btn"
            onClick={handleLogout}
          >
            Logout
          </button>

        ) : (

          /* =============================================
             GUEST USER
          ============================================= */

          <>

            <button
              type="button"
              className="auth-link"
              onClick={handleLogin}
            >
              Login
            </button>

            <button
              type="button"
              className="auth-link"
              onClick={handleRegister}
            >
              Register
            </button>

          </>

        )}

      </div>

    </div>

  );

}


export default Header;