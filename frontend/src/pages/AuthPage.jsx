import React, { useState } from 'react';
import LoginForm from '../components/LoginForm';
import SignupForm from '../components/SignupForm';

function AuthPage({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="auth-page">
      <div className="auth-container">
        {isLogin ? <LoginForm onLoginSuccess={onLoginSuccess} /> : <SignupForm />}
        
        <div className="auth-footer">
          <button 
            onClick={() => setIsLogin(!isLogin)} 
            className="toggle-auth-btn"
          >
            {isLogin ? 'Need an account? Sign Up' : 'Have an account? Login'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
