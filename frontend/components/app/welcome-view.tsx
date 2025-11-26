"use client";

import React, { useEffect, useState } from "react";
import "@/styles/welcome.css";
import {
  Bar
} from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from "chart.js";
ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

interface ProgressData {
  [key: string]: {
    avg_score: number | null;
    times_explained: number;
    times_quizzed: number;
    times_taught_back: number;
  };
}

export default function WelcomeView({
  onStartCall,
}: {
  onStartCall: () => void;
}) {
  const [progress, setProgress] = useState<ProgressData>({});

  const handleStartLearning = () => {
    console.log("Start Exploring Amazon Basics");
    onStartCall?.();
  };

  useEffect(() => {
    fetch("/geography_progress.json")
      .then((res) => res.json())
      .then((data) => {
        setProgress(data);
      })
      .catch(() => console.warn("Progress file not found yet."));
  }, []);

  const getBarChartData = () => {
    const labels = Object.keys(progress);
    const scores = labels.map(t => progress[t].avg_score || 0);

    return {
      labels,
      datasets: [
        {
          label: "Customer Interest Score",
          data: scores,
          backgroundColor: scores.map(score =>
            score >= 80 ? "#146EB4" : score >= 50 ? "#FF9900" : "#D62828"
          ),
          borderWidth: 1,
        },
      ],
    };
  };

  const getProficiencyColor = (score: number | null) => {
    if (score === null) return "progress-badge gray";
    if (score >= 80) return "progress-badge green";
    if (score >= 50) return "progress-badge yellow";
    return "progress-badge red";
  };

  return (
    <div className="welcome-container">
      <section className="welcome-card">
        <h1 className="welcome-title">Amazon Basics Hub 🛒</h1>

        <p className="welcome-subtitle">
          Explore Amazon Basics essentials, track your selections, and manage your shopping insights.
        </p>

        <button className="welcome-button" onClick={handleStartLearning}>
          Start Shopping with Ace 🎙️
        </button>
      </section>

      {Object.keys(progress).length > 0 && (
        <section className="dashboard-section">
          <h2 className="dashboard-title">Your Product Insights 📊</h2>

          {/* Table */}
          <table className="progress-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Interest Level</th>
                <th>Times Viewed</th>
                <th>Times Recommended</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(progress).map(([topic, stats]) => (
                <tr key={topic}>
                  <td>{topic}</td>
                  <td>
                    <span className={getProficiencyColor(stats.avg_score)}>
                      {stats.avg_score ? Math.round(stats.avg_score) + "%" : "—"}
                    </span>
                  </td>
                  <td>{stats.times_quizzed}</td>
                  <td>{stats.times_taught_back}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Bar Chart */}
          <div className="chart-wrapper">
            <Bar data={getBarChartData()} options={{ responsive: true }} />
          </div>
        </section>
      )}
    </div>
  );
}
