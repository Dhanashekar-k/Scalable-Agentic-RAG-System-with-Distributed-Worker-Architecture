import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import SourcesPage from './pages/SourcesPage'
import ChatPage from './pages/ChatPage'
import KnowledgeGraphPage from './pages/KnowledgeGraphPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="graph" element={<KnowledgeGraphPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
