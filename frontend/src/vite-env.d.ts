/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CHAOS_AGENT_API_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
