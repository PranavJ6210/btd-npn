import React, { useState, useEffect } from 'react';
import api from '../api';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

function AccountPage() {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await api.get('/users/me/history');
        setHistory(response.data);
      } catch (err) {
        setError('Failed to fetch prediction history.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (isLoading) {
    return <div>Loading history...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>;
  }

  // --- Process history to count predicted classes ---
  const classCounts = history.reduce((acc, pred) => {
    acc[pred.predicted_class] = (acc[pred.predicted_class] || 0) + 1;
    return acc;
  }, {});

  const chartData = Object.entries(classCounts).map(([label, value]) => ({
    name: label,
    value,
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']; // Add more if needed

  return (
    <div style={{ padding: '20px' }}>
      <h2>Your Prediction History</h2>

     {/* Donut Pie Chart */}
      {chartData.length > 0 ? (
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="40%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                fill="#8884d8"
                label={({ percent }) => `${(percent * 100).toFixed(1)}%`}
              >
                {chartData.map((entry, index) => {
                  const COLOR_MAP = {
                    glioma: "#FFBB28",
                    meningioma: "#0088FE",
                    notumor: "#00C49F",
                    pituitary: "#FF8042",
                  };
                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLOR_MAP[entry.name] || "#8884d8"} // fallback color
                    />
                  );
                })}
              </Pie>
              <Tooltip />
              <Legend
                layout="vertical"
                align="right"
                verticalAlign="middle"
                formatter={(value) => {
                  const total = chartData.reduce((sum, d) => sum + d.value, 0);
                  const thisItem = chartData.find(d => d.name === value);
                  const percent = ((thisItem.value / total) * 100).toFixed(1);
                  return `${value} (${percent}%)`;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p>No predictions yet to display in chart.</p>
      )}

      {/* History Table */}
      {history.length === 0 ? (
        <p>You have not made any predictions yet.</p>
      ) : (
        <table border="1" cellPadding="8" style={{ marginTop: '20px', width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th>Date</th>
              <th>Patient ID</th>
              <th>Patient Name</th>
              <th>Predicted Class</th>
              <th>Confidence</th>
              <th>Image</th>
            </tr>
          </thead>
          <tbody>
            {history.map((pred) => (
              <tr key={pred.id}>
                <td>{new Date(pred.prediction_timestamp).toLocaleString()}</td>
                <td>{pred.patient.patient_id}</td>
                <td>{pred.patient.name}</td>
                <td>{pred.predicted_class}</td>
                <td>{pred.confidence.toFixed(4)}</td>
                <td>
                  <a
                    href={`http://localhost:8000/${pred.image_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View Image
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default AccountPage;
