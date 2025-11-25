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
    console.log("Start Learning Geography");
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
          label: "Average Score",
          data: scores,
          backgroundColor: scores.map(score =>
            score >= 80 ? "#4caf50" : score >= 50 ? "#ffc107" : "#f44336"
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
        <h1 className="welcome-title">Geography Learning Hub 🌍</h1>

        <p className="welcome-subtitle">
          Learn new concepts, test your knowledge, and track your progress!
        </p>

        <button className="welcome-button" onClick={handleStartLearning}>
          Start Learning Geography 🎙️
        </button>
      </section>

      {Object.keys(progress).length > 0 && (
        <section className="dashboard-section">
          <h2 className="dashboard-title">Your Learning Progress 📈</h2>

          {/* Table */}
          <table className="progress-table">
            <thead>
              <tr>
                <th>Topic</th>
                <th>Mastery</th>
                <th>Quizzes</th>
                <th>Teach-backs</th>
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

