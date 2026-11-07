import type { ComponentType, SVGProps } from 'react'
import {
  BotIcon,
  ChatIcon,
  CodeIcon,
  LayersIcon,
  StampIcon,
  WorkflowIcon,
} from '../../shared/ui/elements/Icons'

type Icon = ComponentType<SVGProps<SVGSVGElement>>

export type PageSlug = 'chat' | 'architecture' | 'code' | 'verify'

export interface NavPage {
  slug: PageSlug
  label: string
  icon: Icon
}

/** One screen family, e.g. "Naive RAG". Its pages are the sidebar items and the workspace tabs. */
export interface AppDef {
  id: string // URL segment: /dashboard/<id>/<page>
  label: string
  description: string
  icon: Icon
  pages: NavPage[]
}

export interface NavGroup {
  id: string
  label: string
  icon: Icon
  apps: AppDef[]
  /** Show the (single) app's pages directly under the group, without an app level. */
  flat?: boolean
}

const ragPages: NavPage[] = [
  { slug: 'chat', label: 'Chat & Documents', icon: ChatIcon },
  { slug: 'architecture', label: 'Architecture & Workflow', icon: WorkflowIcon },
  { slug: 'code', label: 'Step-by-Step Code', icon: CodeIcon },
]

// To add a screen family: add an AppDef here, and (optionally) a component in WorkspacePage's registry.
export const navGroups: NavGroup[] = [
  {
    id: 'rag',
    label: 'RAG Applications',
    icon: LayersIcon,
    apps: [
      {
        id: 'naive-rag',
        label: 'Naive RAG',
        description: 'Document-based question answering using vector search and LLM.',
        icon: LayersIcon,
        pages: ragPages,
      },
      {
        id: 'hybrid-rag',
        label: 'Hybrid RAG',
        description: 'Combine keyword and vector search for more accurate retrieval.',
        icon: LayersIcon,
        pages: ragPages,
      },
      {
        id: 'multimodal-rag',
        label: 'Multimodal RAG',
        description: 'Ask questions over documents that include images and tables.',
        icon: LayersIcon,
        pages: ragPages,
      },
    ],
  },
  {
    id: 'llm',
    label: 'LLM Playground',
    icon: BotIcon,
    flat: true,
    apps: [
      {
        id: 'llm-playground',
        label: 'LLM Playground',
        description: 'Chat directly with a language model and experiment with prompts.',
        icon: BotIcon,
        pages: [
          { slug: 'chat', label: 'Model Chat', icon: ChatIcon },
          { slug: 'architecture', label: 'Architecture & Workflow', icon: WorkflowIcon },
          { slug: 'code', label: 'Step-by-Step Code', icon: CodeIcon },
        ],
      },
    ],
  },
]

navGroups.push({
  id: 'document-ai',
  label: 'Document AI',
  icon: StampIcon,
  flat: true,
  apps: [
    {
      id: 'stamp-verification',
      label: 'Stamp Verification',
      description: 'Detect official stamps in a PDF and match them against the reference stamps.',
      icon: StampIcon,
      pages: [
        { slug: 'verify', label: 'Verify a PDF', icon: StampIcon },
        { slug: 'architecture', label: 'Architecture & Workflow', icon: WorkflowIcon },
      ],
    },
  ],
})

export const allApps: AppDef[] = navGroups.flatMap((g) => g.apps)
export const defaultPath = '/dashboard/naive-rag/chat'

export const findApp = (id: string | undefined) => allApps.find((a) => a.id === id)
export const pagePath = (app: AppDef, page: NavPage) => `/dashboard/${app.id}/${page.slug}`
