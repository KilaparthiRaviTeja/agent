import { useState } from "react";

const ApplicationForm = () => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    ssn_last4: "",
    address: "",
    submission_date: new Date().toISOString().split("T")[0], // Auto-fill today's date
  });

  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("http://127.0.0.1:8000/applications/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        throw new Error("Failed to submit application");
      }

      const data = await res.json();
      setResponse(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      setResponse(null);
    }
  };

  return (
    <div className="max-w-lg mx-auto mt-10 p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-semibold mb-4">Application Form</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" name="first_name" placeholder="First Name" value={formData.first_name} onChange={handleChange} required className="w-full p-2 mb-2 border rounded" />
        <input type="text" name="last_name" placeholder="Last Name" value={formData.last_name} onChange={handleChange} required className="w-full p-2 mb-2 border rounded" />
        <input type="date" name="date_of_birth" value={formData.date_of_birth} onChange={handleChange} required className="w-full p-2 mb-2 border rounded" />
        <input type="text" name="ssn_last4" placeholder="Last 4 Digits of SSN" value={formData.ssn_last4} onChange={handleChange} required className="w-full p-2 mb-2 border rounded" />
        <input type="text" name="address" placeholder="Address" value={formData.address} onChange={handleChange} required className="w-full p-2 mb-2 border rounded" />

        <button type="submit" className="w-full bg-blue-500 text-white py-2 rounded">Submit</button>
      </form>

      {response && (
        <div className="mt-4 p-4 bg-green-100 rounded">
          <p>✅ Application Submitted Successfully!</p>
          <p>📅 Estimated Approval Date: <strong>{response.approval_date}</strong></p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-100 rounded">
          <p>❌ {error}</p>
        </div>
      )}
    </div>
  );
};

export default ApplicationForm;
