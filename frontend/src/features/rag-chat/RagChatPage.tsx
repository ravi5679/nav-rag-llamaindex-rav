import { useState } from 'react'
import type { RagType } from '../../shared/endpoints'
import { DocumentUploadPage } from '../document-upload/DocumentUploadPage'
import { ChatPanel } from './components/ChatPanel'
import './rag-chat.css'

type Tab = 'chat' | 'docs'

/**
 * Chat (left) and document upload (right) side by side.
 * On narrow screens the two panels become tabs; both stay mounted so chat history is kept.
 */
export function RagChatPage({ rag }: { rag: RagType }) {
  const [tab, setTab] = useState<Tab>('chat')

  return (
    <div className="rag-workspace" data-tab={tab}>
      <div className="rag-tabs" role="tablist">
        <button className="btn" role="tab" aria-selected={tab === 'chat'} onClick={() => setTab('chat')}>
          Chat
        </button>
        <button className="btn" role="tab" aria-selected={tab === 'docs'} onClick={() => setTab('docs')}>
          Documents
        </button>
      </div>

      <ChatPanel rag={rag} />

      <aside className="panel upload-panel" aria-label="Documents">
        <DocumentUploadPage rag={rag} />
      </aside>
    </div>
  )
}
