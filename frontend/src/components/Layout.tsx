import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen bg-white">
      <main className="max-w-7xl mx-auto px-4 py-4 sm:px-6 sm:py-6 md:px-8 md:py-8">
        <Outlet />
      </main>
    </div>
  )
}
