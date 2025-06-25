import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './css/CourseForm.css';


const CourseForm = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    objectives: '',
    outcomes: '',
    audience: '',
    prerequisites: '',
    contactHours: '',
    homeworkHours: '',
    totalWeeks: '',
    creditType: '',
    manualCredits: ''
  });
  const navigate = useNavigate();
  const [calculatedCredits, setCalculatedCredits] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isValid, setIsValid] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const calculateCredits = () => {
    if (formData.creditType !== 'calculated') return;
    
    const contactHours = parseFloat(formData.contactHours) || 0;
    const homeworkHours = parseFloat(formData.homeworkHours) || 0;
    const totalWeeks = parseFloat(formData.totalWeeks) || 0;
    
    const totalHours = (contactHours + homeworkHours) * totalWeeks;
    const credits = Math.round((totalHours / 15) * 2) / 2; // Round to nearest 0.5
    setCalculatedCredits(credits);
  };

  useEffect(() => {
    calculateCredits();
    validateForm();
  }, [formData]);

  const validateForm = () => {
    const requiredFields = [
      'title', 'description', 'objectives', 'outcomes',
      'audience', 'prerequisites', 'contactHours',
      'homeworkHours', 'totalWeeks', 'creditType'
    ];
    
    const allFieldsFilled = requiredFields.every(field => {
      if (field === 'creditType' && formData[field] === 'manual') {
        return formData.manualCredits.trim() !== '';
      }
      return formData[field].trim() !== '';
    });
    
    setIsValid(allFieldsFilled);
  };

 const handleSubmit = async (e) => {
  e.preventDefault();
  setIsGenerating(true);

  try {
    const payload = {
      course_id: `course_${Date.now()}`,
      title: formData.title,
      prerequisites: formData.prerequisites.split(',').map(p => p.trim()),
      description: formData.description,
      learning_objectives: formData.objectives.split('.').map(o => o.trim()).filter(o => o),
      target_audience: formData.audience,
      duration: `${formData.totalWeeks} weeks`,
      credits: formData.creditType === "calculated" ? calculatedCredits : parseFloat(formData.manualCredits)
    };

    const response = await fetch("http://127.0.0.1:8000/course/generate/outline", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("API response:", data);


    // Store result (you can pick `data.result` or whole response)
localStorage.setItem("generatedCourse", JSON.stringify({ outline: data.result }));

    navigate("/outline");

  } catch (error) {
    console.error(error);
    alert("Failed to generate course. Please try again.");
  } finally {
    setIsGenerating(false);
  }
};


  return (
    <div className="form-column">
      <h1 className="form-title">Welcome to Our AI Course Generator, Let's Get Started.</h1>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Course Title<span  style={{color:'red'}}>*</span></label>
          <input
            type="text"
            className="form-input"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Enter course title"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Brief Course Description<span  style={{color:'red'}}>*</span></label>
          <textarea
            className="form-input form-textarea"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Enter brief course description"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Learning Objectives<span  style={{color:'red'}}>*</span></label>
          <textarea
            className="form-input form-textarea"
            name="objectives"
            value={formData.objectives}
            onChange={handleChange}
            placeholder="Enter learning objectives"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Learning Outcomes<span  style={{color:'red'}}>*</span></label>
          <textarea
            className="form-input form-textarea"
            name="outcomes"
            value={formData.outcomes}
            onChange={handleChange}
            placeholder="Enter learning outcomes"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Target Audience<span  style={{color:'red'}}>*</span></label>
          <input
            type="text"
            className="form-input"
            name="audience"
            value={formData.audience}
            onChange={handleChange}
            placeholder="Enter target audience"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Prerequisites to the Course<span  style={{color:'red'}}>*</span></label>
          <textarea
            className="form-input form-textarea"
            name="prerequisites"
            value={formData.prerequisites}
            onChange={handleChange}
            placeholder="Enter course prerequisites"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Weekly Contact Hours<span  style={{color:'red'}}>*</span></label>
          <input
            type="number"
            className="form-input"
            name="contactHours"
            value={formData.contactHours}
            onChange={handleChange}
            placeholder="Enter weekly contact hours"
            min="0"
            step="0.5"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Homework Hours per Week<span  style={{color:'red'}}>*</span></label>
          <input
            type="number"
            className="form-input"
            name="homeworkHours"
            value={formData.homeworkHours}
            onChange={handleChange}
            placeholder="Enter homework hours per week"
            min="0"
            step="0.5"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Total Weeks<span  style={{color:'red'}}>*</span></label>
          <input
            type="number"
            className="form-input"
            name="totalWeeks"
            value={formData.totalWeeks}
            onChange={handleChange}
            placeholder="Enter total weeks"
            min="1"
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">Credits<span  style={{color:'red'}}>*</span></label>
          <select
  className="form-input form-select"
  name="creditType"
  value={formData.creditType}
  onChange={handleChange}
  required
>
  <option value="" disabled>
    Choose between calculated or manual credit hours *
  </option>
  <option value="calculated">Calculated Credit Hours</option>
  <option value="manual">Manual Override</option>
</select>

        </div>
        
        {formData.creditType === 'manual' && (
          <div className="form-group">
            <label className="form-label">Enter Manual Credit Hours<span  style={{color:'red'}}>*</span></label>
            <input
              type="number"
              className="form-input"
              name="manualCredits"
              value={formData.manualCredits}
              onChange={handleChange}
              placeholder="Enter manual credit hours"
              min="0"
              step="0.5"
              required
            />
          </div>
        )}
        
        {formData.creditType === 'calculated' && (
          <div className="form-group">
            <label className="form-label">Calculated Credit Hours</label>
            <div className="form-input calculated-credits">
              {calculatedCredits} credits
            </div>
          </div>
        )}
        
        <button
          type="submit"
          className="generate-course-btn"
          disabled={!isValid || isGenerating}
        >
          {isGenerating ? (
            <>
              <span className="spinner"></span> Generating...
            </>
          ) : (
            'Generate Course Outline'
          )}
        </button>
      </form>
    </div>
  );
};

export default CourseForm;