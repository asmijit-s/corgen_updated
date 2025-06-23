import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import jsPDF from 'jspdf';
import './css/CourseOutline.css';

const CourseOutline = () => {
  const navigate = useNavigate();

  const [courseData, setCourseData] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editField, setEditField] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);


  useEffect(() => {
    const stored = localStorage.getItem("generatedCourse");
    if (stored) {
      setCourseData(JSON.parse(stored));
    }
  }, []);

  const handleEdit = (field, value) => {
    setEditField(field);
    setIsEditing(true);
    setEditValue(Array.isArray(value) ? value.join('\n') : value);
  };

  const handleSaveField = () => {
    const updatedData = { ...courseData };
    const newValue =
      editField === 'prerequisites' || editField === 'learning_outcomes'
        ? editValue.split('\n').filter((item) => item.trim() !== '')
        : editValue;

    updatedData.outline[editField] = newValue;
    setCourseData(updatedData);
    setIsEditing(false);
    setEditField(null);
    localStorage.setItem("generatedCourse", JSON.stringify(courseData));
  };

  const handleFinalSave = () => {
    if (courseData) {
        setIsSaving(true); // 🔐 disable button
        const modules = [                                                   //API Response format
      {
        "moduleTitle": "Introduction to Machine Learning",
        "moduleDescription": "Fundamentals of ML, types of learning, and basic concepts.",
        "moduleHours": 18,
        "order": 1,
        "id": "mod_1750611231031_1",
        "courseId": "ML303"
      },
      {
        "moduleTitle": "Supervised Learning Algorithms",
        "moduleDescription": "Linear Regression, Logistic Regression, Support Vector Machines, Decision Trees.",
        "moduleHours": 18,
        "order": 2,
        "id": "mod_1750611231031_2",
        "courseId": "ML303"
      },
      {
        "moduleTitle": "Unsupervised Learning Methods",
        "moduleDescription": "Clustering (K-means, hierarchical), dimensionality reduction (PCA).",
        "moduleHours": 15,
        "order": 3,
        "id": "mod_1750611231031_3",
        "courseId": "ML303"
      },
      {
        "moduleTitle": "Model Evaluation & Selection",
        "moduleDescription": "Bias-variance tradeoff, cross-validation, hyperparameter tuning.",
        "moduleHours": 10,
        "order": 4,
        "id": "mod_1750611231031_4",
        "courseId": "ML303"
      },
      {
        "moduleTitle": "Introduction to Deep Learning",
        "moduleDescription": "Neural networks, backpropagation, and common architectures.",
        "moduleHours": 6,
        "order": 5,
        "id": "mod_1750611231031_5",
        "courseId": "ML303"
      },
      {
        "moduleTitle": "Deep Learning Architectures",
        "moduleDescription": "Convolutional Neural Networks (CNNs), Recurrent Neural Networks (RNNs).",
        "moduleHours": 5,
        "order": 6,
        "id": "mod_1750611231031_6",
        "courseId": "ML303"
      }
    ];
    const updatedCourse = {
      ...courseData,
      modules: modules // directly set under key "modules"
    };
      localStorage.setItem("generatedCourse", JSON.stringify(updatedCourse));

      // Simulate 4 second save delay
      setTimeout(() => {
        navigate("/modules");
      }, 4000);
    }
  };
  const handleDownloadPDF = () => {
    if (!courseData) return;
     setIsDownloading(true); // 🔐 disable button

    const doc = new jsPDF();
    const { title, prerequisites, description, learning_outcomes, duration, credits } = courseData.outline;

    doc.setFontSize(16);
    doc.text(`Course Title: ${title}`, 10, 20);
    doc.setFontSize(12);
    doc.text(`Course ID: ${courseData.course_id}`, 10, 30);
    doc.text(`Duration: ${duration}`, 10, 40);
    doc.text(`Credits: ${credits}`, 10, 50);

    doc.text('Prerequisites:', 10, 60);
    prerequisites.forEach((pre, i) => {
      doc.text(`- ${pre}`, 15, 70 + i * 8);
    });

    doc.text('Description:', 10, 90 + prerequisites.length * 8);
    doc.text(doc.splitTextToSize(description, 180), 15, 100 + prerequisites.length * 8);

    const outcomeStartY = 110 + prerequisites.length * 8 + doc.splitTextToSize(description, 180).length * 7;
    doc.text('Learning Outcomes:', 10, outcomeStartY);
    learning_outcomes.forEach((lo, i) => {
      const wrapped = doc.splitTextToSize(`- ${lo}`, 180);
      doc.text(wrapped, 15, outcomeStartY + 10 + i * 10);
    });

    doc.save(`${title.replace(/\s+/g, '_')}_Outline.pdf`);
  };
  const renderEditableField = (label, field, value) => {
    if (isEditing && editField === field) {
      return (
        <div className="edit-container">
          <label className="form-label">{label}</label>
          <textarea
            className="form-input-outline form-textarea-outline"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
          />
          <div className="edit-buttons">
            <button className="build-btn" onClick={handleSaveField}>Save</button>
            <button className="cancel-btn" onClick={() => setIsEditing(false)}>Cancel</button>
          </div>
        </div>
      );
    }

    const displayValue = Array.isArray(value)
      ? value.map((item, i) => <li key={i}>{item}</li>)
      : value;

    return (
      <div className="preview-item" onClick={() => handleEdit(field, value)}>
        <div className="preview-label">
          {label}
          <div className="edit-icon">✏️</div>
        </div>
        <div className="preview-value">
          {Array.isArray(value) ? <ul>{displayValue}</ul> : displayValue}
        </div>
      </div>
    );
  };

  if (!courseData) return <div>Loading course data...</div>;

  return (
    <div className="course-outline-container">
      <div className="header-section">
        <h1 className="course-title">{courseData.outline.title}</h1>
        <div className="course-id">Course ID: {courseData.course_id}</div>
      </div>

      <div className="outline-section">
        {renderEditableField("Course Title", "title", courseData.outline.title)}
        {renderEditableField("Prerequisites", "prerequisites", courseData.outline.prerequisites)}
        {renderEditableField("Description", "description", courseData.outline.description)}
        {renderEditableField("Learning Outcomes", "learning_outcomes", courseData.outline.learning_outcomes)}
        {renderEditableField("Duration", "duration", courseData.outline.duration)}
        {renderEditableField("Credits", "credits", courseData.outline.credits)}
      </div>

      <div className="action-buttons">
        <button className="save-continue-btn" onClick={handleFinalSave} disabled={isSaving}>
           {isSaving ? "Saving..." : "Save Course Outline"}
        </button>
        <button className="download-pdf-btn" onClick={handleDownloadPDF} disabled={isDownloading}>
          {isDownloading ? "Downloading..." : "Download as PDF"}
        </button>
      </div>
    </div>
  );
};

export default CourseOutline;
