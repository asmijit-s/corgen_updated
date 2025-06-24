// App.js
import React, { useState, useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import CourseGenerationProgress from "./components/JourneySteps.jsx";
import ModificationSelector from "./components/UserInputPanel.jsx";
import CourseOutline from "./components/CourseOutline.jsx";
import CourseForm from "./components/CourseForm.jsx";
import ModulesPage from "./components/ModulePage.jsx";
import ModulesListPage from "./components/ModulesListPage.jsx";
import SubmodulesPage from "./components/SubModule.jsx";
import ActivitiesPage from "./components/Activtity.jsx";
import ModulesDropdownPage from "./components/ModuleDropdown.jsx";
import BlueprintPage from "./components/Blueprint.jsx";
import { FiChevronUp, FiChevronDown } from 'react-icons/fi'; // add this at the top
import NotFoundPage from "./components/NotFound.jsx";
import "./App.css";

function generateOptionsFromLocalStorage(context = 'outline') {
  const raw = localStorage.getItem("generatedCourse");
  if (!raw) return [];
  const data = JSON.parse(raw);

  if (context === 'outline' && data.outline) {
    const options = Object.keys(data.outline).map(key => ({
      label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: key,
      fullValue: data.outline[key]
    }));
    return [{ label: "All", value: "all", fullValue: data.outline }, ...options];
  }

  if (context === 'modules' && data.modules) {
    const options = Object.entries(data.modules).map(([key, value]) => ({
      label: value.moduleTitle,
      value: key,
      fullValue: value
    }));
    return [{ label: "All", value: "all", fullValue: data.modules }, ...options];
  }
  if (context === 'submodules') {
    const path = window.location.pathname;
    const match = path.match(/\/submodules\/(\d+)/);
    const moduleIndex = match ? parseInt(match[1]) : null;

    if (
      moduleIndex !== null &&
      Array.isArray(data.modules) &&
      data.modules[moduleIndex]?.submodules
    ) {
      const submods = data.modules[moduleIndex].submodules;
      const options = submods.map((sub, idx) => ({
        label: sub.submoduleName,
        value: `${moduleIndex}_${idx}`,
        fullValue: sub
      }));
      return [{ label: "All", value: "all", fullValue: submods }, ...options];
    }
  }
  if (context === 'activities') {
    const path = window.location.pathname;
    const match = path.match(/\/activities\/(\d+)\/(\d+)/);
    const moduleIndex = match ? parseInt(match[1]) : null;
    const submoduleIndex = match ? parseInt(match[2]) : null;

    if (
      moduleIndex !== null &&
      submoduleIndex !== null &&
      Array.isArray(data.modules) &&
      data.modules[moduleIndex]?.submodules &&
      data.modules[moduleIndex].submodules[submoduleIndex]?.activities
    ) {
      const activities = data.modules[moduleIndex].submodules[submoduleIndex].activities;
      const options = activities.map((activity, idx) => ({
        label: activity.activityName || `Activity ${idx + 1}`,
        value: `${moduleIndex}_${submoduleIndex}_${idx}`,
        fullValue: activity
      }));
      return [{ label: "All", value: "all", fullValue: activities }, ...options];
    }
  }
  return [];
}

function AppContent() {
  const location = useLocation();
  const [options, setOptions] = useState([]);
  const [leftPanelWidth, setLeftPanelWidth] = useState(300);
  const isResizing = useRef(false);
  const [isCollapsed, setIsCollapsed] = useState(false); // NEW

  const toggleCollapse = () => setIsCollapsed(prev => !prev);
  
  const handleMouseDown = () => { isResizing.current = true; };
  const handleMouseMove = (e) => {
    if (!isResizing.current) return;
    setLeftPanelWidth(Math.max(200, Math.min(e.clientX, 600)));
  };
  const handleMouseUp = () => { isResizing.current = false; };

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  useEffect(() => {
    if (location.pathname.includes("/outline")) {
      setOptions(generateOptionsFromLocalStorage("outline"));
    } else if (location.pathname.includes("/modules")) {
      setOptions(generateOptionsFromLocalStorage("modules"));
    } else if(location.pathname.includes("/submodules/")){
      setOptions(generateOptionsFromLocalStorage("submodules"));
    }else if (location.pathname.includes("/activities/")) {
      setOptions(generateOptionsFromLocalStorage("activities"));
    } else {
      setOptions([]);
    }
  }, [location.pathname]);

  const handleModificationSubmit = (selectedKey, prompt) => {
    const selectedOption = options.find(opt => opt.value === selectedKey);
    const value = selectedOption?.fullValue || "";

    console.log("Selected key:", selectedKey);
    console.log("Associated value:", value);
    console.log("Prompt:", prompt);
    // Future: Call API with key, value, and prompt
  };

  return (
    <div className="app-container">
      <Navbar />
      <div className="main-layout">
        <div className="left-panel" style={{ width: leftPanelWidth }}>
          <CourseGenerationProgress />
          {/* Collapsible Header */}
          <div 
            className="modification-toggle-header"
            onClick={toggleCollapse}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '8px 12px',
              backgroundColor: 'rgb(0 160 255)',
              borderBottom: '1px solid #ddd',
              cursor: 'pointer',
              height: 'fit-content',
              width:'-webkit-fill-available',
              color:'white'
            }}
          >
            <span><strong>Modify Content</strong></span>
            {isCollapsed ? <FiChevronDown /> : <FiChevronUp />}
          </div>

          {/* Conditionally show ModificationSelector */}
          {!isCollapsed && (
            <ModificationSelector 
              options={options.map(({ label, value }) => ({ label, value }))} 
              onSubmit={handleModificationSubmit} 
            />
          )}
        </div>
        <div className="drag-handle" onMouseDown={handleMouseDown} style={{ left: leftPanelWidth - 2 }} />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<CourseForm />} />
            <Route path="/outline" element={<CourseOutline />} />
            <Route path="/modules" element={<ModulesPage />} />
            <Route path="/submodules" element={<ModulesListPage />} />
            <Route path="/submodules/:id" element={<SubmodulesPage />} />
            <Route path="/activities" element={<ModulesDropdownPage />} />
            <Route path="/activities/:moduleId/:submoduleId" element={<ActivitiesPage />} />
            <Route path="/blueprint" element={<BlueprintPage />} />
            <Route path="/:nothing" element={<NotFoundPage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
