"use client";

import React from "react";
import "@/styles/welcome.css";

export default function WelcomeView({
  onStartCall,
}: {
  onStartCall: () => void;
}) {
  const handleStartCheckin = () => {
    console.log("START CHECK-IN CLICKED");
    if (typeof onStartCall === "function") {
      onStartCall();
    } else {
      console.warn("❌ onStartCall not received!");
    }
  };

  return (
    <div className="welcome-container">
      <div className="circle"></div>
      <div className="circle"></div>
      <div className="circle"></div>
      <div className="circle"></div>

      <section className="welcome-card">
        <h1 className="welcome-title">
          Daily Wellness Check-In 🌱
        </h1>

        <p className="welcome-subtitle">
          A few minutes just for you — to notice how you're doing, set gentle intentions,
          and take a moment of care.
        </p>

        <ul className="welcome-list">
          <li>Mood & energy reflection</li>
          <li>1–3 small daily intentions</li>
          <li>Guided voice check-in</li>
        </ul>

        <button className="welcome-button" onClick={handleStartCheckin}>
          Start Voice Check-In 🎙️
        </button>

        <p className="welcome-footer-text">
          Not medical or diagnostic — just support for your wellbeing.
        </p>
      </section>
    </div>
  );
}

