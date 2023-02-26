import axios from 'axios';
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
axios.defaults.headers.post['Content-Type'] = 'application/json';
// axios.defaults.baseURL = 'http://0.0.0.0:8080/';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
