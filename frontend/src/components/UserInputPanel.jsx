import React, { useState } from 'react';
import './css/ModificationSelector.css';

const ModificationSelector = ({ 
  dropdownLabel = "Select a section to re-build",
  textareaLabel = "Describe your changes",
  placeholder = "Enter your prompt to re-build here...",
  submitButtonText = "Re-build",
  cancelButtonText = "Cancel",
  options = [],
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const [selectedOption, setSelectedOption] = useState('');
  const [modificationText, setModificationText] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!selectedOption) {
      setError('Please select an option');
      return;
    }
    if (!modificationText.trim()) {
      setError('Please describe your changes');
      return;
    }

    const selected = options.find(opt => opt.value === selectedOption);
    const fullValue = selected?.fullValue;
    console.log(`Processing your request with the following:
\nSelected Key: ${selected.label}
\nFull Value: ${typeof fullValue === 'object' ? JSON.stringify(fullValue, null, 2) : fullValue}
\nYour Prompt: ${modificationText}`);
    alert(
      `Processing your request with the following:
\nSelected Key: ${selected.label}
\nFull Value: ${typeof fullValue === 'object' ? JSON.stringify(fullValue, null, 2) : fullValue}
\nYour Prompt: ${modificationText}`
    );

    setError('');
    try {
      await onSubmit(selectedOption, modificationText);
      setSelectedOption('');
      setModificationText('');
    } catch (err) {
      setError('Failed to submit changes. Please try again.');
    }
  };

  return (
    <div className="modification-section">
      {/* <div className="form-group-modification">
        <label className="form-label-modification">{dropdownLabel}</label>
        <select 
          className="select-dropdown-modification" 
          value={selectedOption}
          onChange={(e) => setSelectedOption(e.target.value)}
          disabled={isLoading}
        >
          <option value="">Select an option...</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div> */}

      <div className="form-group-modification">
        <label className="form-label-modification">{textareaLabel}</label>
        <textarea 
          className="modification-textarea-modification" 
          value={modificationText}
          onChange={(e) => setModificationText(e.target.value)}
          placeholder={placeholder}
          disabled={isLoading}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="action-buttons">
        <button 
          className="build-btn" 
          onClick={handleSubmit}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span> Processing...
            </>
          ) : (
            submitButtonText
          )}
        </button>
        <button 
          className="cancel-btn" 
          onClick={onCancel}
          disabled={isLoading}
        >
          {cancelButtonText}
        </button>
      </div>
    </div>
  );
};

export default ModificationSelector;
