import React, { useState } from "react";
import "./App.css";

const ApplicationForm = () => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    ssn_last4: "",
    household_size: "",
    income: "",
    address: "",
    is_enrolled_in_program: false,
    program_name: "",
  });

  const [errors, setErrors] = useState({});
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // Validation function
  const validateForm = () => {
    const newErrors = {};
    if (!formData.first_name.trim()) newErrors.first_name = "First Name is required";
    if (!formData.last_name.trim()) newErrors.last_name = "Last Name is required";
    if (!formData.date_of_birth) newErrors.date_of_birth = "Date of Birth is required";
    if (!/^\d{4}$/.test(formData.ssn_last4)) newErrors.ssn_last4 = "SSN must be 4 digits";
    if (!formData.household_size || isNaN(formData.household_size) || formData.household_size < 1 || formData.household_size > 8) {
      newErrors.household_size = "Household size must be between 1 and 8";
    }
    if (!formData.income || isNaN(formData.income) || formData.income <= 0) newErrors.income = "Valid Income is required";
    if (!formData.address.trim()) newErrors.address = "Address is required";
    if (formData.is_enrolled_in_program && !formData.program_name.trim()) newErrors.program_name = "Program Name is required if enrolled";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input change
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({ ...formData, [name]: type === "checkbox" ? checked : value });
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validateForm()) {
      setErrorMessage("Please fix the errors before submitting.");
      return;
    }
    setShowModal(true);
  };

  // Confirm submission to backend
  const confirmSubmission = async () => {
    setShowModal(false);
    setLoading(true);
    setErrors({});
    setErrorMessage("");

    try {
      const res = await fetch("http://localhost:8000/applications/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong");

      console.log("API Response:", data); // Debugging: Check response in console
      setResponse(data);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Clear form function
  const handleClear = () => {
    setFormData({
      first_name: "",
      last_name: "",
      date_of_birth: "",
      ssn_last4: "",
      household_size: "",
      income: "",
      address: "",
      is_enrolled_in_program: false,
      program_name: "",
    });
    setErrors({});
    setErrorMessage("");
    setResponse(null);
  };

  return (
    <div className="main-container">
      <div className="container">
        <h2>Application Form</h2>
        <form onSubmit={handleSubmit} className="form">
          <input type="text" name="first_name" placeholder="First Name" value={formData.first_name} onChange={handleChange} required />
          {errors.first_name && <p className="error-text">{errors.first_name}</p>}

          <input type="text" name="last_name" placeholder="Last Name" value={formData.last_name} onChange={handleChange} required />
          {errors.last_name && <p className="error-text">{errors.last_name}</p>}

          <input type="date" name="date_of_birth" value={formData.date_of_birth} onChange={handleChange} required />
          {errors.date_of_birth && <p className="error-text">{errors.date_of_birth}</p>}

          <input type="text" name="ssn_last4" placeholder="Last 4 digits of SSN" value={formData.ssn_last4} onChange={handleChange} maxLength="4" required />
          {errors.ssn_last4 && <p className="error-text">{errors.ssn_last4}</p>}

          <input 
  type="text" 
  name="household_size" 
  placeholder="Number of People in Household (1-9)" 
  value={formData.household_size} 
  onChange={handleChange} 
  maxLength="1" 
  pattern="[1-9]" 
  onInput={(e) => e.target.value = e.target.value.replace(/[^1-9]/g, '')} 
  required 
/>
{errors.household_size && <p className="error-text">{errors.household_size}</p>}


          <input type="text" name="income" placeholder="Income (in $)" value={formData.income} onChange={handleChange} required />
          {errors.income && <p className="error-text">{errors.income}</p>}

          <input type="text" name="address" placeholder="Address" value={formData.address} onChange={handleChange} required />
          {errors.address && <p className="error-text">{errors.address}</p>}

          <div>
            <label>
              Are you enrolled in a qualifying government assistance program?
              <input type="checkbox" name="is_enrolled_in_program" checked={formData.is_enrolled_in_program} onChange={handleChange} />
            </label>
            {formData.is_enrolled_in_program && (
              <div>
                <input type="text" name="program_name" placeholder="Enter the program name" value={formData.program_name} onChange={handleChange} />
                {errors.program_name && <p className="error-text">{errors.program_name}</p>}
              </div>
            )}
          </div>

          <button type="submit" disabled={loading}>{loading ? "Submitting..." : "Submit"}</button>

          <button type="button" onClick={handleClear} disabled={loading}>Clear</button>

          {errorMessage && <p className="error-text">{errorMessage}</p>}
        </form>
      </div>

      <div className="submission-details">
        <h2>Submission Details</h2>
        {response ? (
          <div className="response">
            <p><strong>Submission Date:</strong> {response.submission_date || "Not Available"}</p>
            <p><strong>Status:</strong> {response.status || "Pending"}</p>
            <p><strong>Approval ETA:</strong> {response.approval_eta ? `${response.approval_eta} days` : "Not Available"}</p>
            <p><strong>Estimated Approval Date:</strong> {response.approval_estimated_date || "Not Available"}</p>
            <p><strong>Approval Date:</strong> {response.approval_date || "N/A"}</p>
          </div>
        ) : (
          <p>No submissions yet.</p>
        )}
      </div>

      {showModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Confirm Submission</h3>
            <p>Are you sure you want to submit the application?</p>
            <button onClick={confirmSubmission}>Yes, Submit</button>
            <button onClick={() => setShowModal(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationForm;
