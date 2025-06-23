import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft } from 'react-icons/fi';
import './css/Activity.css';

const activityTypes = [
  { value: 'lecture', label: 'Lecture' },
  { value: 'quiz', label: 'Quiz' },
  { value: 'assignment', label: 'Assignment' },
  { value: 'lab', label: 'Lab' },
  { value: 'reading', label: 'Reading' }
];

const ActivitiesPage = () => {
  const { moduleId, submoduleId } = useParams();
  const navigate = useNavigate();
  const [activities, setActivities] = useState([]);
  const [editingIndex, setEditingIndex] = useState(null);
  const [editForm, setEditForm] = useState({ activityName: '', activityDescription: '', activityObjective: '', activityType: 'lecture' });
  const [showAddModal, setShowAddModal] = useState(false);
  const [newActivity, setNewActivity] = useState({ activityName: '', activityDescription: '', activityObjective: '', activityType: 'lecture' });
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [guidelines, setGuidelines] = useState('');
  const [showForm, setShowForm] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("generatedCourse");
    if (stored) {
        const parsed = JSON.parse(stored);
        const module = parsed.modules[moduleId];
        if (module && module.submodules && module.submodules[submoduleId]) {
        const submodule = module.submodules[submoduleId];
        const act = submodule.activities || [];
        setActivities(act);
        if (act.length > 0) {
            setShowForm(false);
        }
        }
    }
    }, [moduleId, submoduleId]);

  const handleGenerateActivities = () => {
    const mockActivities = [
      {
        activityName: "Understanding the Basics of Supervised Learning",
        activityDescription: "This lecture introduces the fundamental concept of supervised learning...",
        activityObjective: "Learners will be able to define supervised learning...",
        activityType: "lecture"
      },
      {
        activityName: "Differentiating Supervised Learning",
        activityDescription: "This lecture contrasts supervised learning with other paradigms...",
        activityObjective: "Learners will be able to differentiate supervised learning...",
        activityType: "lecture"
      },
      {
        activityName: "Common Applications of Supervised Learning",
        activityDescription: "This lecture explores real-world scenarios...",
        activityObjective: "Learners will be able to identify applications...",
        activityType: "lecture"
      },
      {
        activityName: "Supervised Learning Fundamentals Quiz",
        activityDescription: "This short quiz assesses understanding of supervised learning...",
        activityObjective: "Learners will be able to answer questions about fundamental concepts...",
        activityType: "quiz"
      },
      {
        activityName: "Machine Learning Type Identification Quiz",
        activityDescription: "This quiz asks learners to identify the appropriate learning type...",
        activityObjective: "Learners will be able to classify scenarios correctly...",
        activityType: "quiz"
      }
    ];

    const stored = localStorage.getItem("generatedCourse");
    if (!stored) return;
    const parsed = JSON.parse(stored);
    const submodules = parsed.modules[moduleId].submodules || [];
    submodules[submoduleId].activities = mockActivities;
    parsed.modules[moduleId].submodules = submodules;
    localStorage.setItem("generatedCourse", JSON.stringify(parsed));
    setActivities(mockActivities);
    setShowForm(false);
  };

  const handleEdit = (index) => {
    const activity = activities[index];
    setEditingIndex(index);
    setEditForm({ ...activity });
  };

  const handleSave = () => {
    const updatedActivities = [...activities];
    updatedActivities[editingIndex] = { ...editForm };
    saveActivities(updatedActivities);
    setEditingIndex(null);
  };

  const handleDelete = (index) => {
    if (window.confirm("Are you sure you want to delete this activity?")) {
      const updatedActivities = [...activities];
      updatedActivities.splice(index, 1);
      saveActivities(updatedActivities);
    }
    window.location.reload();
  };

  const handleAddActivity = () => {
    if (!newActivity.activityName || !newActivity.activityDescription || !newActivity.activityObjective) {
      alert("Please fill in all required fields");
      return;
    }
    const updatedActivities = [...activities, { ...newActivity }];
    saveActivities(updatedActivities);
    setNewActivity({ activityName: '', activityDescription: '', activityObjective: '', activityType: 'lecture' });
    setShowAddModal(false);
    window.location.reload();
  };

  const saveActivities = (updatedActivities) => {
    const stored = localStorage.getItem("generatedCourse");
    if (stored) {
      const parsed = JSON.parse(stored);
      parsed.modules[moduleId].submodules[submoduleId].activities = updatedActivities;
      localStorage.setItem("generatedCourse", JSON.stringify(parsed));
      setActivities(updatedActivities);
    }
  };

  const getActivityTypeColor = (type) => {
    switch(type) {
      case 'lecture': return '#6b46c1';
      case 'quiz': return '#10b981';
      case 'assignment': return '#3b82f6';
      case 'lab': return '#f59e0b';
      case 'reading': return '#64748b';
      default: return '#6b46c1';
    }
  };

  return (
    <div className="activities-container">
      {showForm && (
        <div className="generate-form">
          <h2>Select Activity Types and Guidelines</h2>
          <div className="form-group">
            <label>Choose Types*</label>
            <div className="checkbox-group">
              {activityTypes.map(type => (
                <label key={type.value}>
                  <input
                    type="checkbox"
                    value={type.value}
                    checked={selectedTypes.includes(type.value)}
                    onChange={(e) => {
                      const val = e.target.value;
                      setSelectedTypes(prev => prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val]);
                    }}
                  />
                  {type.label}
                </label>
              ))}
            </div>
          </div>
          <div className="form-group">
            <label>Guidelines</label>
            <textarea
              value={guidelines}
              onChange={(e) => setGuidelines(e.target.value)}
              placeholder="Add instructions for generating activities..."
            />
          </div>
          <button className="generate-btn" onClick={handleGenerateActivities}>Generate Activities</button>
        </div>
      )}

      {!showForm && (
        <>
          <div className="activities-header">
            <button className="back-btn" onClick={() => navigate(-1)}>
              <FiArrowLeft /> Back to Submodules
            </button>
            <h1>Activities</h1>
            <button className="add-activity-btn" onClick={() => setShowAddModal(true)}>
              + Add Activity
            </button>
          </div>

          <div className="activities-list">
            {activities.map((activity, index) => (
              <div key={index} className="activity-card">
                {editingIndex === index ? (
                  <div className="activity-edit-form">
                    <div className="form-group">
                      <label>Activity Name*</label>
                      <input type="text" value={editForm.activityName} onChange={(e) => setEditForm({...editForm, activityName: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Activity Type*</label>
                      <select value={editForm.activityType} onChange={(e) => setEditForm({...editForm, activityType: e.target.value})}>
                        {activityTypes.map(type => (
                          <option key={type.value} value={type.value}>{type.label}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Description*</label>
                      <textarea value={editForm.activityDescription} onChange={(e) => setEditForm({...editForm, activityDescription: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Objective*</label>
                      <textarea value={editForm.activityObjective} onChange={(e) => setEditForm({...editForm, activityObjective: e.target.value})} />
                    </div>
                    <div className="form-buttons">
                      <button className="save-btn" onClick={handleSave}>Save</button>
                      <button className="cancel-btn" onClick={() => setEditingIndex(null)}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="activity-header">
                      <div style={{display:'flex', justifyContent: 'space-between'}}>
                        <h3>{activity.activityName}</h3>
                        <span className="activity-type-badge" style={{ backgroundColor: getActivityTypeColor(activity.activityType) }}>
                          {activityTypes.find(t => t.value === activity.activityType)?.label || 'Activity'}
                        </span>
                      </div>
                      <div className="activity-actions">
                        <button className="edit-btn" onClick={() => handleEdit(index)}>Edit</button>
                        <button className="delete-btn" onClick={() => handleDelete(index)}>Delete</button>
                      </div>
                    </div>
                    <div className="activity-description">{activity.activityDescription}</div>
                    <div className="activity-objective"><strong>Objective:</strong> {activity.activityObjective}</div>
                  </>
                )}
              </div>
            ))}

            {activities.length === 0 && (
              <div className="empty-activities">No activities yet. Click "Add Activity" to create one.</div>
            )}
          </div>
        </>
      )}

      {showAddModal && (
        <div className="modal-overlay">
          <div className="modal-box">
            <h2>Add New Activity</h2>
            <div className="form-group">
              <label>Activity Name*</label>
              <input type="text" value={newActivity.activityName} onChange={(e) => setNewActivity({...newActivity, activityName: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Activity Type*</label>
              <select value={newActivity.activityType} onChange={(e) => setNewActivity({...newActivity, activityType: e.target.value})}>
                {activityTypes.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Description*</label>
              <textarea value={newActivity.activityDescription} onChange={(e) => setNewActivity({...newActivity, activityDescription: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Objective*</label>
              <textarea value={newActivity.activityObjective} onChange={(e) => setNewActivity({...newActivity, activityObjective: e.target.value})} />
            </div>
            <div className="modal-buttons">
              <button className="save-btn" onClick={handleAddActivity}>Add Activity</button>
              <button className="cancel-btn" onClick={() => setShowAddModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivitiesPage;
