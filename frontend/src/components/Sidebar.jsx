import React from "react";
import { Link } from "react-router-dom";

function Sidebar({ onLogout, userEmail }) {
  return (
    <aside className="sidebar">
      {/* Top section: Header and Navigation */}
      <div className="sidebar-top">
        <div className="sidebar-header">
          <h2>NeuroScan</h2>
          <p>Diagnosis Assistant</p>
        </div>
        <nav>
          <ul>
            <li>
              <Link to="/home">Home</Link>
            </li>
            <li>
              <Link to="/predict">Predict</Link>
            </li>
            <li>
              <Link to="/account">Account</Link>
            </li>
          </ul>
        </nav>
      </div>

      {/* Bottom section: User Info and Logout */}
      <div className="sidebar-bottom">
        <div className="user-info">
          <span>{userEmail || "user@example.com"}</span>
        </div>
        <button onClick={onLogout} className="logout-button">
          Logout
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;