import React, { useState, useEffect } from "react";
import axios from "axios";
import { Paper } from "@mui/material";

const UserHistory = () => {
  const [predictions, setPredictions] = useState([]);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await axios.get(
          process.env.REACT_APP_SERVER_ENDPOINT + "/predictions"
        );
        setPredictions(response.data);
      } catch (error) {
        console.error("Error while fetching predictions:", error);
      }
    };

    fetchPredictions();
  }, []); // Empty array ensures useEffect runs only once (on mount)

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        maxWidth: "1000px",
      }}
    >
      <Paper
        elevation={3}
        style={{ padding: "20px", backgroundColor: "#1A353E", width: "100%" }}
      >
        <h2
          style={{
            color: "#D9D9D9",
            marginBottom: "10px",
            textAlign: "center",
          }}
        >
          History
        </h2>
        <Paper
          elevation={3}
          style={{
            maxHeight: "400px",
            overflowY: "auto",
            padding: "20px",
            backgroundColor: "#D9D9D9",
          }}
        >
          <ul style={{ listStyle: "none", padding: 0 }}>
            {predictions.map((prediction) => (
              <li key={prediction.id} style={{ marginBottom: "20px" }}>
                <div
                  style={{
                    display: "flex",
                    height: "70px",
                    backgroundColor: "white",
                    borderRadius: "8px",
                    overflow: "hidden",
                  }}
                >
                  <div style={{ height: "70px", width: "70px" }}>
                    <img
                      src={`data:image/jpeg;base64,${prediction.image}`}
                      alt="Prediction"
                      style={{
                        width: "70px",
                        height: "70px",
                        objectFit: "cover",
                      }}
                    />
                  </div>
                  <div style={{ padding: "10px", fontSize: "small" }}>
                    <p>Prediction: {prediction.score}</p>
                    <p>Created At: {prediction.created_at}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </Paper>
      </Paper>
    </div>
  );
};

export default UserHistory;
