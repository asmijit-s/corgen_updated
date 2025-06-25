import React, { useState, useRef, useEffect } from "react";
import { useLocation } from "react-router-dom";
import "./css/SuggestionBox.css";

const getStageFromPath = (path) => {
  if (path.includes("/outline")) return "outlines";
  if (path.includes("/modules")) return "modules";
  if (path.includes("/submodules/")) return "submodules";
  if (path.includes("/activities/")) return "activities";
  return null;
};

const SuggestionWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const panelRef = useRef(null);
  const location = useLocation();

  const stage = getStageFromPath(location.pathname);
  const isVisible = !!stage;

  // Load suggestions from localStorage when stage or pathname changes
 useEffect(() => {
  if (stage) {
    const raw = localStorage.getItem("generatedCourse");
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        const key = `suggestions_${stage}`;
        const suggestionsObj = parsed[key];
        const suggestionsList = Array.isArray(suggestionsObj?.suggestions) ? suggestionsObj.suggestions : [];
        setSuggestions(suggestionsList);
      } catch (err) {
        console.error("Error parsing course data for suggestions:", err);
        setSuggestions([]);
      }
    }
  }
}, [stage, location.pathname]);


  // Handle outside click to close the panel
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  if (!isVisible) return null;

  return (
    <div className="suggestion-widget">
      {!isOpen && (
        <div className="floating-btn" onClick={() => setIsOpen(true)}>
          View Suggestions
        </div>
      )}

      {isOpen && (
        <div className="suggestion-panel" ref={panelRef}>
          <div className="suggestion-header">
            <h4>Suggestions</h4>
            <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
          </div>
          {suggestions.length > 0 ? (
            <ul>
              {suggestions.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          ) : (
            <p>No suggestions available for this stage.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default SuggestionWidget;
