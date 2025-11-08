/// <reference types="vite/client" />

// 可选：声明自定义环境变量，便于智能提示
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}


