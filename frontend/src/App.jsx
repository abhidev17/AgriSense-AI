import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { DiagnosisProvider } from './context/DiagnosisContext'
import { useToast } from './hooks/useToast'
import Navbar from './components/Navbar/Navbar'
import ToastContainer from './components/Toast/Toast'
import Home from './pages/Home/Home'
import Diagnosis from './pages/Diagnosis/Diagnosis'
import Loading from './pages/Loading/Loading'
import Dashboard from './pages/Dashboard/Dashboard'
import History from './pages/History/History'
import NotFound from './pages/NotFound/NotFound'

function AppContent() {
  const { toasts, toast, removeToast } = useToast()

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/"          element={<Home />} />
        <Route path="/diagnose"  element={<Diagnosis toast={toast} />} />
        <Route path="/loading"   element={<Loading />} />
        <Route path="/dashboard" element={<Dashboard toast={toast} />} />
        <Route path="/history"   element={<History toast={toast} />} />
        <Route path="*"          element={<NotFound />} />
      </Routes>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <DiagnosisProvider>
        <AppContent />
      </DiagnosisProvider>
    </BrowserRouter>
  )
}
