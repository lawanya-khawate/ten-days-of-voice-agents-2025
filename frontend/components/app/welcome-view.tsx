"use client";

import React from "react";
import "@/styles/welcome.css";
import { Mic } from "lucide-react";

export default function WelcomeView({
  onStartCall,
}: {
  onStartCall: () => void;
}) {
  return (
    <div className="hero-wrapper">

      {/* NAV BAR */}
      <nav className="hero-nav">
        <div className="logo">SoftUI Voice Agent</div>

        <div className="nav-links">
          <span>Home</span>
          <span>Features</span>
          <span>How it Works</span>
          <span>Contact</span>
        </div>

        <button className="nav-btn">Launch App</button>
      </nav>

      {/* MAIN HERO */}
      <section className="hero-grid">

        {/* LEFT SIDE */}
        <div className="hero-left">
          <h1 className="hero-title">
            Order Anything <br />
            Using Your <span className="highlight-text">Voice</span>
          </h1>

          <p className="hero-subtitle">
            A pastel-soft, modern AI voice agent for food & grocery ordering.
            Powered by Murf Falcon TTS + LiveKit real-time understanding.
          </p>

          <div className="hero-buttons">
            <button className="start-btn" onClick={onStartCall}>
              Start Ordering
            </button>

            <button className="learn-btn">Watch Demo →</button>
          </div>
        </div>

        {/* RIGHT SIDE — ORB WITH MIC */}
        <div className="hero-orb-container">
          <div className="hero-orb">
            <Mic className="mic-icon" />
          </div>
        </div>

      </section>

      {/* FEATURE CARDS */}
      <section className="features-section">
        <div className="feature-card">
          🥗 <h3>Food Ordering</h3>
          <p>Order your meals from any app using just your voice.</p>
        </div>

        <div className="feature-card">
          🛒 <h3>Grocery Shopping</h3>
          <p>Add items to your cart, compare prices, track availability.</p>
        </div>

        <div className="feature-card">
          🚚 <h3>Track Orders</h3>
          <p>Know live updates of your Swiggy, Zomato, or Zepto orders.</p>
        </div>
      </section>
    </div>
  );
}
