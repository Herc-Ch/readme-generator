import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import "./App.css";
import { ThemeProvider } from "./components/theme-provider";
// import Layout from "./components/layout";

// App.jsx
import ModeToggle from "@/components/mode-toggle";

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      {/* make it impossible to miss */}
      <div className="fixed top-4 right-4 z-50">
        <ModeToggle />
      </div>

      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
