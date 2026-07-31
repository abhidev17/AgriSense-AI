import { createContext, useContext, useState } from 'react'

const DiagnosisContext = createContext(null)

export function DiagnosisProvider({ children }) {
  const [diagnosisResult, setDiagnosisResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const clearResult = () => setDiagnosisResult(null)

  return (
    <DiagnosisContext.Provider value={{
      diagnosisResult,
      setDiagnosisResult,
      isLoading,
      setIsLoading,
      clearResult,
    }}>
      {children}
    </DiagnosisContext.Provider>
  )
}

export const useDiagnosis = () => {
  const ctx = useContext(DiagnosisContext)
  if (!ctx) throw new Error('useDiagnosis must be inside DiagnosisProvider')
  return ctx
}
