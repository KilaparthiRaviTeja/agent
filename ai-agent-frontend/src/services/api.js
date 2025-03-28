import axios from "axios";

const API_BASE_URL = "https://ai-agent-x90k.onrender.com"; // Replace with your actual backend URL

export const submitApplication = async (data) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/applications/`, data);
    return response.data;
  } catch (error) {
    console.error("Error submitting application:", error);
    throw error;
  }
};

export const getApplications = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/applications/`);
    return response.data;
  } catch (error) {
    console.error("Error fetching applications:", error);
    throw error;
  }
};
