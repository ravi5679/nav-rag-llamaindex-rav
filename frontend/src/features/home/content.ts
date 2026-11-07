// All editable site copy lives here. Replace the placeholder links with your own.
export const profile = {
  name: 'Ravi Kumar',
  profession: 'Software Developer',
  tagline: 'Building practical AI solutions, one agent at a time',
  expertise: [
    'AI agent development (Claude & OpenAI APIs)',
    'RAG systems',
    'React + TypeScript',
    'Python / FastAPI',
    'Oracle PL/SQL',
    '.NET',
  ],
  links: {
    linkedin: 'https://www.linkedin.com/in/your-handle', // placeholder
    github: 'https://github.com/your-handle', // placeholder
    email: 'mailto:you@example.com', // placeholder
  },
  emailLabel: 'you@example.com', // placeholder
}

export const heroChips = ['Claude API', 'OpenAI', 'RAG', 'FastAPI', 'React + TS']

export const learnTopics = [
  {
    title: 'LLM Basics',
    text: 'How large language models work: tokens, context windows, embeddings and why they sometimes get things wrong.',
  },
  {
    title: 'Prompt Engineering',
    text: 'Write prompts that are clear, testable and repeatable: roles, examples, structure and output formats.',
  },
  {
    title: 'RAG Systems',
    text: 'Chunk, embed and retrieve your own documents so answers are grounded in your data, with sources.',
  },
  {
    title: 'AI Agents',
    text: 'Give models tools and a loop: planning, tool calling and guardrails with the Claude and OpenAI APIs.',
  },
  {
    title: 'Build the Backend',
    text: 'Ship an AI API with Python and FastAPI: streaming, auth, background work and tracing.',
  },
  {
    title: 'Build the Frontend',
    text: 'Turn it into a product with React and TypeScript: chat UIs, uploads and a clean dashboard.',
  },
]

export const projects = [
  {
    title: 'RAG Document Chat',
    text: 'Upload PDFs and docs, then ask questions and get answers with the source passages. Built with LlamaIndex, FastAPI and React. This site is the front end.',
    tags: ['LlamaIndex', 'FastAPI', 'React'],
    href: 'https://github.com/your-handle/rag-app', // placeholder
  },
  {
    title: 'Tool-Using AI Agent',
    text: 'An agent that plans, calls tools and checks its own results, using the Claude API tool-use loop.',
    tags: ['Claude API', 'Agents', 'Python'],
    href: 'https://github.com/your-handle/ai-agent', // placeholder
  },
  {
    title: 'AI over Enterprise Data',
    text: 'Connecting LLMs to existing business data, from Oracle PL/SQL and .NET systems, safely and with an audit trail.',
    tags: ['OpenAI', 'Oracle PL/SQL', '.NET'],
    href: 'https://github.com/your-handle/enterprise-ai', // placeholder
  },
]
