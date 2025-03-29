import React, { useState, useEffect, useRef } from "react";
import "./App.css";

const ApplicationForm = () => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    date_of_birth: "",
    ssn_last4: "",
    address: "",
  });

  const [errors, setErrors] = useState({});
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const firstNameRef = useRef(null);
  const ssnRef = useRef(null);

  useEffect(() => {
    if (firstNameRef.current) {
      firstNameRef.current.focus();
    }
  }, []);

  const validateForm = () => {
    let newErrors = {};

    if (!formData.first_name.trim()) newErrors.first_name = "First Name is required";
    if (!formData.last_name.trim()) newErrors.last_name = "Last Name is required";
    if (!formData.date_of_birth) newErrors.date_of_birth = "Date of Birth is required";
    if (!/^\d{4}$/.test(formData.ssn_last4)) newErrors.ssn_last4 = "SSN must be 4 digits (numbers only)";
    if (!formData.address.trim()) newErrors.address = "Address is required";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;

    // Allow only letters and spaces for first_name & last_name
    if ((name === "first_name" || name === "last_name") && !/^[A-Za-z\s]*$/.test(value)) {
      return;
    }

    // Ensure SSN field only contains numbers
    if (name === "ssn_last4" && !/^\d*$/.test(value)) {
      return;
    }

    setFormData({ ...formData, [name]: value });

    if (errors[name]) {
      validateForm();
    }

    if (name === "ssn_last4" && value.length === 4) {
      ssnRef.current?.blur();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validateForm()) {
      setErrorMessage("Please fix the errors before submitting.");
      return;
    }

    setShowModal(true);
  };

  const confirmSubmission = async () => {
    setShowModal(false);
    setLoading(true);
    setErrors({});
    setErrorMessage("");

    try {
      const res = await fetch("http://localhost:8000/applications/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong");

      setResponse(data);
      setFormData({ first_name: "", last_name: "", date_of_birth: "", ssn_last4: "", address: "" });
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      first_name: "",
      last_name: "",
      date_of_birth: "",
      ssn_last4: "",
      address: "",
    });
    setErrors({});
    setErrorMessage("");
    setResponse(null);
  };

  return (
    <div className="main-container">
      {/* Left Side: Application Form */}
      <div className="container">
        <h2>Application Form</h2>
        <form onSubmit={handleSubmit} className="form">
          <input
            ref={firstNameRef}
            type="text"
            name="first_name"
            placeholder="First Name"
            value={formData.first_name}
            onChange={handleChange}
            className={errors.first_name ? "input-error" : ""}
            required
          />
          {errors.first_name && <p className="error-text">{errors.first_name}</p>}

          <input
            type="text"
            name="last_name"
            placeholder="Last Name"
            value={formData.last_name}
            onChange={handleChange}
            className={errors.last_name ? "input-error" : ""}
            required
          />
          {errors.last_name && <p className="error-text">{errors.last_name}</p>}

          <input
            type="date"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={handleChange}
            className={errors.date_of_birth ? "input-error" : ""}
            required
          />
          {errors.date_of_birth && <p className="error-text">{errors.date_of_birth}</p>}

          <input
            ref={ssnRef}
            type="text"
            name="ssn_last4"
            placeholder="Last 4 digits of SSN"
            value={formData.ssn_last4}
            onChange={handleChange}
            maxLength="4"
            className={errors.ssn_last4 ? "input-error" : ""}
            required
          />
          {errors.ssn_last4 && <p className="error-text">{errors.ssn_last4}</p>}

          <input
            type="text"
            name="address"
            placeholder="Address"
            value={formData.address}
            onChange={handleChange}
            className={errors.address ? "input-error" : ""}
            required
          />
          {errors.address && <p className="error-text">{errors.address}</p>}

          <button type="submit" disabled={loading}>{loading ? "Submitting..." : "Submit"}</button>
          <button type="button" onClick={handleReset}>Reset</button>

          {errorMessage && <p className="error-text">{errorMessage}</p>}
        </form>
      </div>

      {/* Right Side: Submission Details */}
      <div className="submission-details">
        <h2>Submission Details</h2>
        {response ? (
          <div className="response">
            <p><strong>Submission Date:</strong> {response.submission_date}</p>
            <p><strong>Status:</strong> {response.status}</p>
            <p><strong>Approval ETA:</strong> {response.approval_eta} days</p>
            <p><strong>Estimated Approval Date:</strong> {response.approval_estimated_date}</p>
            <p><strong>Approval Date:</strong> {response.approval_date || "N/A"}</p>
          </div>
        ) : (
          <p>No submissions yet.</p>
        )}
      </div>

      {/* Confirmation Modal */}
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
