import React, { useState } from 'react';
import axios from 'axios';

function LoginForm({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      
      const response = await axios.post('http://localhost:8000/token', params);
      
      onLoginSuccess(response.data.access_token);
      setMessage('Login successful!');
    } catch (error) {
      setMessage('Error logging in: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      <div>
        <label>Email:</label>
        <input 
          type="email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required 
        />
      </div>
      <div>
        <label>Password:</label>
        <input 
          type="password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
        />
      </div>
      <button type="submit">Login</button>
      {message && <p>{message}</p>}
    </form>
  );
}

export default LoginForm;