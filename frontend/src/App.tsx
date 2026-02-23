import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Plan from './pages/Plan'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Plan />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
