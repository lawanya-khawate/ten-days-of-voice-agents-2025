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

      {/* ----------------------------------------------------
          NAV BAR
      ---------------------------------------------------- */}
      <nav className="hero-nav">
        <div className="logo">STATION • FALL</div>

        <div className="nav-links">
          <span>Overview</span>
          <span>Signal Log</span>
          <span>Protocols</span>
          <span>About</span>
        </div>

        <button className="nav-btn">Access System</button>
      </nav>


      {/* ----------------------------------------------------
          MAIN HUD GRID (LEFT - CENTER - RIGHT)
      ---------------------------------------------------- */}
      <section className="hud-grid">

        {/* ----------------------------------------------------
            LEFT COLUMN — HOLOGRAM PANELS
        ---------------------------------------------------- */}
        <div className="left-panels">

          <div className="holo-panel">
            <div className="panel-title">GALACTIC MAP SCAN</div>
            <div className="panel-visual"></div>
            <div className="holo-grid"></div>
          </div>

          <div className="holo-panel" style={{ marginTop: "24px" }}>
            <div className="panel-title">QUANTUM WAVEFORM</div>
            <div className="panel-visual"></div>
            <div className="holo-grid"></div>
          </div>

          <div className="holo-panel" style={{ marginTop: "24px" }}>
            <div className="panel-title">ENVIRONMENTAL METRICS</div>
            <div className="panel-visual"></div>
            <div className="holo-grid"></div>
          </div>

        </div>


        {/* ----------------------------------------------------
            CENTER COLUMN — ORB, RINGS, TITLE, CTA
        ---------------------------------------------------- */}
        <div className="center-hero">

          {/* Rotating Rings */}
          <div className="ring ring-1"></div>
          <div className="ring ring-2"></div>

          {/* Central Orb */}
          <div className="orb">
            {/* AI Core SVG */}
            <svg
              className="ai-core"
              viewBox="0 0 100 100"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="50" cy="50" r="26" strokeOpacity="0.8" />
              <path d="M50 18 L50 5 M50 95 L50 82" strokeOpacity="0.6" />
              <path d="M18 50 L5 50 M95 50 L82 50" strokeOpacity="0.6" />
              <circle cx="50" cy="50" r="8" fill="currentColor" opacity="0.9" />
            </svg>
          </div>

          {/* Title */}
          <h1 className="hero-title">
            The Silence Before<br />The Signal
          </h1>

          {/* Subtitle */}
          <p className="hero-subtitle">
            You awaken in a fractured orbit. Systems failing.  
            A signal pulses in the dark—  
            <span style={{ color: "var(--primary)" }}>not human, not alone.</span>
          </p>

          {/* CTA Button */}
          <button className="start-btn" onClick={onStartCall}>
            Initiate Contact
          </button>

        </div>


        {/* ----------------------------------------------------
            RIGHT COLUMN — HOLOGRAM PANELS
        ---------------------------------------------------- */}
        <div className="right-panels">

          <div className="holo-panel">
            <div className="panel-title">REACTOR CORE STATUS</div>
            <div className="panel-visual"></div>
            <div className="holo-grid"></div>
          </div>

          <div className="holo-panel" style={{ marginTop: "24px" }}>
            <div className="panel-title">ALIEN FREQUENCY ANALYZER</div>
            <div className="panel-visual"></div>
            <div className="holo-grid"></div>
          </div>

          <div className="holo-panel" style={{ marginTop: "24px" }}>
            <div className="panel-title">TRAJECTORY MEMORY LOG</div>
            <div className="panel-visual"></div>
            <div className="holo-grid"></div>
          </div>

        </div>

      </section>
    </div>
  );
}
