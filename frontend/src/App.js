import React from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import BasicAuthWrapper from './components/BasicAuthWrapper';
import Navbar from './components/Navbar';
import FeedbackBanner from './components/FeedbackBanner';
import Footer from './components/Footer';
import Home from './pages/Home';
import About from './pages/About';
import Committee from './pages/Committee';
import Amenities from './pages/Amenities';
import Gallery from './pages/Gallery';
import Contact from './pages/Contact';
import HelpDesk from './pages/HelpDesk';
import Login from './pages/Login';
import LoginInfo from './pages/LoginInfo';
import AdminPortal from './pages/AdminPortal';
import Feedback from './pages/Feedback';

function App() {
  return (
    <BasicAuthWrapper>
      <div className="App">
        <BrowserRouter>
          <AuthProvider>
            <Navbar />
            <FeedbackBanner />
            <div className="pt-12">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/about" element={<About />} />
                <Route path="/committee" element={<Committee />} />
                <Route path="/amenities" element={<Amenities />} />
                <Route path="/gallery" element={<Gallery />} />
                <Route path="/help-desk" element={<HelpDesk />} />
                <Route path="/contact" element={<Contact />} />
                <Route path="/login-info" element={<LoginInfo />} />
                <Route path="/login" element={<Login />} />
                <Route path="/feedback" element={<Feedback />} />
                <Route path="/admin" element={<AdminPortal />} />
              </Routes>
            </div>
            <Footer />
          </AuthProvider>
        </BrowserRouter>
      </div>
    </BasicAuthWrapper>
  );
}

export default App;