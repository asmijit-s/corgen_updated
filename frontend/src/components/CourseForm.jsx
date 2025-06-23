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

  const handleSubmit = (e) => {
  e.preventDefault();
  setIsGenerating(true);

  // Simulate backend generation delay
  setTimeout(() => {
    const hardcodedCourseJSON = {
      message: "Course initialized",
      course_id: "ML303",
      outline: {
        course_id: "ML301",
        title: "MachineLearning",
        prerequisites: ["basic programming"],
        description: "This comprehensive 'Machine Learning' course is tailored for 3rd-year undergraduate students, providing a robust journey from foundational machine learning concepts to advanced algorithms and applications. It aims to equip students with the theoretical knowledge and practical skills necessary to tackle both industry-level challenges and explore research-oriented problems in the field. Students will delve into supervised, unsupervised, and deep learning paradigms, model evaluation, and practical implementation strategies. Basic programming proficiency is a prerequisite for this course.",
        learning_outcomes: [
          "Students will be able to articulate the fundamental principles and concepts of various machine learning paradigms, including supervised, unsupervised, and reinforcement learning.",
          "Students will be able to implement, train, and evaluate a range of machine learning models using common programming libraries for practical applications.",
          "Students will be able to critically assess and select appropriate machine learning algorithms for diverse real-world datasets and problems encountered in industry.",
          "Students will be able to analyze and interpret the performance metrics of machine learning models, identifying potential biases and limitations.",
          "Students will be able to understand the mathematical underpinnings of advanced machine learning techniques, preparing them for further research exploration.",
          "Students will be able to apply problem-solving skills to complex machine learning scenarios, demonstrating an understanding of both theoretical foundations and practical deployment considerations."
        ],
        duration: "12 weeks",
        credits: 5
      }
    };

    // Save to localStorage
    localStorage.setItem("generatedCourse", JSON.stringify(hardcodedCourseJSON));

    // Navigate to /outline
    navigate("/outline");
  }, 2000); // simulate loading time
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
            <option value="">Choose between calculated or manual credit hours<span  style={{color:'red'}}>*</span></option>
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