/* Tipos de entorno (patrón Vite). Declara import.meta.env sin requerir
   la dependencia `vite/client`, para que tsc/tsup compilen las .d.ts. */
interface ImportMetaEnv {
  readonly VITE_ANALYTICS_API?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
