import { BrowserRouter, Routes, Route } from "react-router-dom";

import AIMode from "./pages/AIMode";
import Login from "./pages/Login";
import Register from "./pages/Register";

import ESSAIWidget from "./components/ESSAIWidget";


function App() {

  return (

    <BrowserRouter>

      <Routes>

        {/* =================================================
            FLOATING ESS AI

            The normal homepage is ONLY the floating widget.
            AIMode is opened by ESSAIWidget.
        ================================================= */}

        <Route
          path="/"
          element={
            <div className="app-page">
              <ESSAIWidget />
            </div>
          }
        />


        {/* =================================================
            FULL AI MODE

            Keep this route available for testing.
        ================================================= */}

        <Route
          path="/ai"
          element={<AIMode />}
        />


        {/* =================================================
            LOGIN
        ================================================= */}

        <Route
          path="/login"
          element={<Login />}
        />


        {/* =================================================
            REGISTER
        ================================================= */}

        <Route
          path="/register"
          element={<Register />}
        />

      </Routes>

    </BrowserRouter>

  );

}


export default App;