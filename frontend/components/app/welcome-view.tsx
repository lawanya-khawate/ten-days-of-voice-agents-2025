"use client";

import React from "react";
import "@/styles/welcome.css";

export default function WelcomeView({
  onStartCall,
}: {
  onStartCall: () => void;
}) {
  return (
    <div className="hero-wrapper">
      
      {/* NAV BAR */}
      <nav className="hero-nav">
        <div className="logo">LSK Bank AI</div>
        <div className="nav-links">
          <span>Home</span>
          <span>About</span>
          <span>Security</span>
          <span>Contact</span>
        </div>
        <button className="nav-btn">Launch App</button>
      </nav>

      {/* HERO SECTION */}
      <section className="hero-flex">

        {/* LEFT TEXT */}
        <div className="hero-left">
          <h1 className="hero-title">
            <span>AI-Powered</span><br />
            Fraud Detection<br />
            <span className="highlight-text">for LSK Bank</span>
          </h1>

          <p className="hero-subtitle">
            Safeguard every transaction with real-time anomaly detection,
            advanced pattern intelligence, and enterprise-grade security.
          </p>

          <div className="hero-buttons">
            <button className="start-btn" onClick={onStartCall}>
              Begin Fraud Analysis
            </button>
            <button className="learn-btn">Learn More →</button>
          </div>
        </div>

        {/* CENTER SHIELD & GLOW */}
        <div className="hero-center">
          <div className="shield-glow-effect"></div>
          <svg className="shield-svg" viewBox="0 0 64 64" fill="none">
            <path
              d="M32 4L8 14V30C8 45 18 55 32 60C46 55 56 45 56 30V14L32 4Z"
              stroke="#3FA9F5"
              strokeWidth="3"
              fill="rgba(63,169,245,0.15)"
              filter="url(#shadow)"
            />
          </svg>

          <div className="shield-reflection"></div>
        </div>

        {/* RIGHT DECORATIVE WAVES */}
        <div className="hero-right">
          <div className="wave wave1"></div>
          <div className="wave wave2"></div>
          <div className="wave wave3"></div>
        </div>

      </section>

      {/* INFO PANEL */}
      <section className="info-panel">
        <div className="panel-icon">🛡️</div>
        <p>
          LSK Bank’s AI reduces the risk of fraudulent attacks by analyzing
          transaction behavior, identifying suspicious patterns, and blocking
          unauthorized access instantly.
        </p>
        <span className="panel-link">Learn more →</span>
      </section>

    </div>
  );
}


