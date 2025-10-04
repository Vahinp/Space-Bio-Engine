import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './routes/Dashboard'
import Study from './routes/Study'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/study/:id" element={<Study />} />
      </Routes>
    </Router>
  )
}

export default App
