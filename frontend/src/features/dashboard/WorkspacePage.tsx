import type { ComponentType } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { HybridRagArchitecturePage } from '../rag-architecture/HybridRagArchitecturePage'
import { NaiveRagArchitecturePage } from '../rag-architecture/NaiveRagArchitecturePage'
import { StampArchitecturePage } from '../rag-architecture/StampArchitecturePage'
import { RagChatPage } from '../rag-chat/RagChatPage'
import { HybridRagCodePage, NaiveRagCodePage } from '../rag-code/RagCodePage'
import { StampVerificationPage } from '../stamp-verification/StampVerificationPage'
import { defaultPath, findApp } from './menu'

// Separate components per RAG type, so switching between Naive and Hybrid starts a fresh chat
const NaiveRagChatPage = () => <RagChatPage rag="naive" />
const HybridRagChatPage = () => <RagChatPage rag="hybrid" />

// Screens that exist so far, keyed "<appId>/<pageSlug>". Everything else shows a placeholder.
const implemented: Record<string, ComponentType> = {
  'naive-rag/chat': NaiveRagChatPage,
  'naive-rag/architecture': NaiveRagArchitecturePage,
  'naive-rag/code': NaiveRagCodePage,
  'hybrid-rag/chat': HybridRagChatPage,
  'hybrid-rag/architecture': HybridRagArchitecturePage,
  'hybrid-rag/code': HybridRagCodePage,
  'stamp-verification/verify': StampVerificationPage,
  'stamp-verification/architecture': StampArchitecturePage,
}

/** /dashboard/<app> without a page: open that app's first page (not every app has "chat"). */
export function AppIndexRedirect() {
  const app = findApp(useParams().appId)
  return <Navigate to={app ? app.pages[0].slug : defaultPath} replace />
}

function ComingSoon({ title }: { title: string }) {
  return (
    <div className="coming-soon">
      <h2>{title}</h2>
      <p className="muted">This section isn't built yet.</p>
    </div>
  )
}

export function WorkspacePage() {
  const { appId, pageId } = useParams()
  const app = findApp(appId)
  const page = app?.pages.find((p) => p.slug === pageId)
  if (!app || !page) return <Navigate to={`/dashboard/${appId ?? ''}`} replace />

  const Page = implemented[`${app.id}/${page.slug}`]
  return Page ? <Page /> : <ComingSoon title={`${app.label} · ${page.label}`} />
}
