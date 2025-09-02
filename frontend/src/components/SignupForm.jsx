import React, { useState } from 'react';
import axios from 'axios';

function SignupForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      // Send a POST request to the backend
      const response = await axios.post('http://localhost:8000/users', {
        email: email,
        password: password
      });
      setMessage(`Signup successful for ${response.data.email}! You can now log in.`);
    } catch (error) {
      // Handle errors, like if the email is already registered
      setMessage('Error signing up: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Sign Up</h2>
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
      <button type="submit">Sign Up</button>
      {message && <p>{message}</p>} {/* Display success or error messages */}
    </form>
  );
}

export default SignupForm;