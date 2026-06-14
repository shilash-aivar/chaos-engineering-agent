import { useState } from 'react'
import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import {
  usePluginsEbpf,
  usePluginsWasm,
  usePolicyPostureRules,
  usePolicyRuntime,
  usePolicyYaml,
  useSavePolicyYaml,
} from '@/hooks/usePlatform'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'

export function PoliciesPage() {
  const runtime = usePolicyRuntime()
  const rules = usePolicyPostureRules()
  const yaml = usePolicyYaml()
  const wasm = usePluginsWasm()
  const ebpf = usePluginsEbpf()
  const saveYaml = useSavePolicyYaml()
  const [policyYaml, setPolicyYaml] = useState('')
  const [dirty, setDirty] = useState(false)

  if (runtime.isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-96 rounded-lg" />
      </PageShell>
    )
  }

  const yamlText = policyYaml || yaml.data?.yaml || ''

  return (
    <PageShell>
      <PageHeader
        title="Policies"
        description="Runtime safety limits enforced by the referee — hard gates, not LLM."
        badge={<Badge variant="outline">live enforcement</Badge>}
      />

      <Tabs defaultValue="runtime">
        <TabsList>
          <TabsTrigger value="runtime">Runtime limits</TabsTrigger>
          <TabsTrigger value="posture">Posture rules</TabsTrigger>
          <TabsTrigger value="plugins">Wasm / eBPF</TabsTrigger>
          <TabsTrigger value="yaml">Policy YAML</TabsTrigger>
        </TabsList>

        <TabsContent value="runtime" className="space-y-6">
          <section className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-sm font-semibold">Active safety policies</h2>
            </div>
            <div className="divide-y divide-border">
              {(runtime.data?.policies ?? []).map((policy) => (
                <div key={policy.id} className="flex flex-wrap items-start justify-between gap-3 px-5 py-4">
                  <div>
                    <p className="text-sm font-medium">{policy.name}</p>
                    <p className="text-xs text-muted-foreground">{policy.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{policy.value}</Badge>
                    <Badge variant={policy.enforced ? 'success' : 'secondary'}>
                      {policy.enforced ? 'enforced' : 'optional'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-sm font-semibold">Executor allowlist</h2>
            </div>
            <div className="divide-y divide-border">
              {(runtime.data?.executors ?? []).map((ex) => (
                <div key={ex.name} className="flex justify-between px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium">{ex.name}</p>
                    <p className="text-xs text-muted-foreground">{ex.detail}</p>
                  </div>
                  <Badge variant={ex.status === 'enabled' ? 'success' : 'secondary'}>{ex.status}</Badge>
                </div>
              ))}
            </div>
          </section>
        </TabsContent>

        <TabsContent value="posture">
          <section className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-sm font-semibold">Posture rule catalog</h2>
            </div>
            <div className="divide-y divide-border">
              {(rules.data?.rules ?? []).map((rule) => (
                <div key={rule.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
                  <div>
                    <p className="font-mono text-xs text-muted-foreground">{rule.id}</p>
                    <p className="text-sm">{rule.summary}</p>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="outline">{rule.scope}</Badge>
                    <Badge variant={rule.severity === 'critical' ? 'destructive' : 'warning'}>
                      {rule.severity}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </TabsContent>

        <TabsContent value="plugins" className="space-y-4">
          <section className="surface-card rounded-lg p-5">
            <h2 className="text-sm font-semibold">Wasm plugins</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Runtime: {wasm.data?.runtime ?? '…'} · {wasm.data?.enabled ? 'enabled' : 'disabled'}
            </p>
            <div className="mt-3 space-y-2">
              {(wasm.data?.plugins ?? []).map((plugin) => (
                <div key={plugin.id} className="flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium">{plugin.name}</p>
                    {plugin.description && (
                      <p className="text-xs text-muted-foreground">{plugin.description}</p>
                    )}
                  </div>
                  <Badge variant="outline">{plugin.runtime}</Badge>
                </div>
              ))}
            </div>
          </section>
          <section className="surface-card rounded-lg p-5">
            <h2 className="text-sm font-semibold">eBPF executor</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {ebpf.data?.enabled ? 'Enabled' : 'Disabled'} · TC netem: {ebpf.data?.use_tc ? 'on' : 'off'} ·{' '}
              {ebpf.data?.active_count ?? 0} active program(s)
            </p>
          </section>
        </TabsContent>

        <TabsContent value="yaml">
          <section className="surface-card rounded-lg p-5">
            <div className="mb-4 flex items-center justify-between gap-2">
              <h2 className="text-sm font-semibold">resilience-policy.yaml</h2>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setPolicyYaml(yaml.data?.yaml ?? '')
                    setDirty(false)
                  }}
                >
                  Reset
                </Button>
                <Button
                  size="sm"
                  disabled={!dirty || saveYaml.isPending}
                  onClick={async () => {
                    await saveYaml.mutateAsync(yamlText)
                    setDirty(false)
                  }}
                >
                  Save to server
                </Button>
              </div>
            </div>
            <Textarea
              className="min-h-[420px] font-mono text-xs"
              value={yamlText}
              onChange={(e) => {
                setPolicyYaml(e.target.value)
                setDirty(true)
              }}
            />
            <p className="mt-2 text-[10px] text-muted-foreground">
              {dirty ? 'Unsaved local edits.' : 'Loaded from server.'}
              {saveYaml.isSuccess ? ' Saved.' : ''}
            </p>
          </section>
        </TabsContent>
      </Tabs>
    </PageShell>
  )
}
