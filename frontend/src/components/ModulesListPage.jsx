import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowRight } from 'react-icons/fi';
import './css/ModulesListPage.css';

const ModulesListPage = () => {
  const [modules, setModules] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const stored = localStorage.getItem("generatedCourse");
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.modules) {
        setModules(parsed.modules);
      }
    }
  }, []);

  const handleModuleClick = (index) => {
    const submodules = [
      {
        submoduleName: "Introduction to Supervised Learning",
        submoduleDescription: "This submodule lays the groundwork for supervised learning, explaining its core principles. You will learn how it differs from other machine learning types and its common applications."
      },
      {
        submoduleName: "Understanding Regression Models",
        submoduleDescription: "Delve into regression, a fundamental supervised learning technique used for predicting continuous outcomes. This submodule covers the basic concepts and types of regression problems."
      }
    ];

    const updatedModules = [...modules];
    updatedModules[index] = {
      ...updatedModules[index],
      submodules: submodules
    };

    setModules(updatedModules);

    const courseData = JSON.parse(localStorage.getItem("generatedCourse")) || {};
    courseData.modules = updatedModules;
    localStorage.setItem("generatedCourse", JSON.stringify(courseData));

    navigate(`/submodules/${index}`);
  };

  return (
    <div className="modules-container">
      <div className="modules-header">
        <h1>Create Submodules</h1>
      </div>

      <div className="modules-list">
        {modules.map((module, index) => (
          <div key={index} className="module-card" onClick={() => handleModuleClick(index)}>
            <div className="module-content">
              <div className="module-info">
                <h3 className="module-title">{module.moduleTitle}</h3>
                <div className="module-description">{module.moduleDescription}</div>
                <div className="module-hours">
                  Duration: <span>{module.moduleHours}</span> hours
                  {module.submodules && (
                    <span className="submodules-count">
                      • {module.submodules.length} submodules
                    </span>
                  )}
                </div>
              </div>
              <div className="module-arrow-container">
                <span className="module-arrow-text">{(module.submodules && module.submodules.length > 0) ? "Manage" : "Create"} Submodules</span><FiArrowRight className="module-arrow-icon" />
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="modules-footer">
        <button
          className="generate-course-btn"
          onClick={() => navigate('/activities')}
          disabled={!modules.every(mod => mod.submodules && mod.submodules.length > 0)}
          style={{ opacity: modules.every(mod => mod.submodules && mod.submodules.length > 0) ? 1 : 0.5 }}
        >
          Save & Continue
        </button>
      </div>
    </div>
  );
};

export default ModulesListPage;
