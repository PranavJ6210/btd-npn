import React, { useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
  useLocation,
} from "react-router-dom";

import HomePage from "./pages/HomePage";
import PredictPage from "./pages/PredictPage";
import AccountPage from "./pages/AccountPage";
import AuthPage from "./pages/AuthPage";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";

import "./App.css";

function App() {
  const [token, setToken] = useState(localStorage.getItem("userToken") || null);

  const AppContent = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const handleLoginSuccess = (newToken) => {
      localStorage.setItem("userToken", newToken);
      setToken(newToken);
      navigate("/home");
    };

    const handleLogout = () => {
      localStorage.removeItem("userToken");
      setToken(null);
      navigate("/auth");
    };

    const isAuthPage = location.pathname === "/auth";

    return (
      <div className="app-container">
        {/* Show Sidebar only when logged in and not on /auth */}
        {token && !isAuthPage && <Sidebar onLogout={handleLogout} />}

        <main className="app-content">
          <Routes>
            {/* Auth route */}
            <Route
              path="/auth"
              element={<AuthPage onLoginSuccess={handleLoginSuccess} />}
            />

            {/* Protected routes */}
            <Route
              path="/home"
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/predict"
              element={
                <ProtectedRoute>
                  <PredictPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/account"
              element={
                <ProtectedRoute>
                  <AccountPage />
                </ProtectedRoute>
              }
            />

            {/* Default redirect */}
            <Route
              path="/"
              element={
                token ? (
                  <HomePage />
                ) : (
                  <AuthPage onLoginSuccess={handleLoginSuccess} />
                )
              }
            />
          </Routes>
        </main>
      </div>
    );
  };

  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
