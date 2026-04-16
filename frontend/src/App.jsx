import React from 'react'
import './index.css'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/chat/ChatPanel'

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <ChatPanel />
    </div>
  )
}
