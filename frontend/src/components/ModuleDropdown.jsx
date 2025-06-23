import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiChevronDown, FiChevronUp, FiArrowRight } from 'react-icons/fi';
import './css/Activity.css';

const ModulesDropdownPage = () => {
  const [modules, setModules] = useState([]);
  const [expandedModule, setExpandedModule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const stored = localStorage.getItem("generatedCourse");

    if (stored) {
      const parsed = JSON.parse(stored);
      setModules(parsed.modules || []);
      setLoading(false);
    } else {
      const simulatedModules = [
        {
          moduleTitle: "Supervised Learning",
          moduleHours: 10,
          submodules: [
            {
              submoduleName: "Introduction to Supervised Learning",
              submoduleDescription:
                "This submodule lays the groundwork for supervised learning, explaining its core principles."
            },
            {
              submoduleName: "Understanding Regression Models",
              submoduleDescription:
                "Covers basic concepts and types of regression problems used in supervised learning."
            }
          ]
        },
        {
          moduleTitle: "Unsupervised Learning",
          moduleHours: 8,
          submodules: [
            {
              submoduleName: "Clustering Basics",
              submoduleDescription: "Explore algorithms like K-means and hierarchical clustering."
            }
          ]
        }
      ];

      setModules(simulatedModules);
      localStorage.setItem("generatedCourse", JSON.stringify({ modules: simulatedModules }));
      setLoading(false);
    }
  }, []);

  const toggleModule = (moduleId) => {
    setExpandedModule(expandedModule === moduleId ? null : moduleId);
  };

  const allActivitiesGenerated = modules.every(module =>
    module.submodules?.every(sub => Array.isArray(sub.activities) && sub.activities.length > 0)
  );

  if (loading) return <div className="loading-spinner">Loading modules...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  return (
    <div className="modules-dropdown-container">
      <div className="modules-header">
        <h1>Manage Activities by Submodule</h1>
      </div>

      <div className="modules-dropdown-list">
        {modules.map((module, moduleIndex) => (
          <div key={moduleIndex} className="module-dropdown-item">
            <div 
              className="module-header-activity"
              onClick={() => toggleModule(moduleIndex)}
            >
              <div className="module-title-container">
                <h3>{module.moduleTitle}</h3>
                <span className="module-hours">{module.moduleHours} hours</span>
              </div>
              <div className="module-actions">
                {expandedModule === moduleIndex ? <FiChevronUp /> : <FiChevronDown />}
              </div>
            </div>

            {expandedModule === moduleIndex && (
              <div className="submodules-list">
                {module.submodules?.length > 0 ? (
                  module.submodules.map((submodule, submoduleIndex) => (
                    <div 
                      key={submoduleIndex} 
                      className="submodule-item"
                    >
                      <div className="submodule-info">
                        <h4>{submodule.submoduleName}</h4>
                        <p className="submodule-description">{submodule.submoduleDescription}</p>
                      </div>
                      <div className="submodule-actions">
                        <button
                          className="edit-btn"
                          onClick={() => navigate(`/activities/${moduleIndex}/${submoduleIndex}`)}
                        >
                          <span>{submodule.activities?.length > 0 ? "Manage" : "Create"} Activities</span>
                          <FiArrowRight />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-submodules">
                    No submodules available in this module.
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Save & Continue Button */}
      <div style={{ marginTop: '2rem', textAlign: 'center' }}>
        <button 
          className="generate-course-btn" 
          onClick={() => navigate("/blueprint")} 
          disabled={!allActivitiesGenerated}
        >
          Save & Continue
        </button>
      </div>
    </div>
  );
};

export default ModulesDropdownPage;
