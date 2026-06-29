import { useEffect, useState } from 'react'
import { Loader2, Save } from 'lucide-react'
import { toast } from 'sonner'
import { useConnectorConfig, useSaveConnectorConfig } from '@/hooks/usePlatform'
import type { ConnectorField } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

type Props = {
  integrationId: string
  onSaved?: () => void
}

export function ConnectorConfigForm({ integrationId, onSaved }: Props) {
  const configQuery = useConnectorConfig(integrationId)
  const saveMutation = useSaveConnectorConfig()
  const [draft, setDraft] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!configQuery.data) return
    const initial: Record<string, string> = {}
    for (const field of configQuery.data.fields) {
      const raw = configQuery.data.values[field.key]
      initial[field.key] = typeof raw === 'string' && !field.secret ? raw : ''
    }
    setDraft(initial)
  }, [configQuery.data])

  if (configQuery.isLoading) {
    return <p className="text-xs text-muted-foreground">Loading connector settings…</p>
  }
  if (!configQuery.data) return null

  const handleSave = async () => {
    try {
      await saveMutation.mutateAsync({ id: integrationId, values: draft })
      toast.success('Connector saved — settings apply immediately')
      onSaved?.()
    } catch {
      toast.error('Failed to save connector')
    }
  }

  return (
    <div className="mt-4 space-y-3 border-t border-border pt-4">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
        Configure from console · source: {configQuery.data.source}
      </p>
      {configQuery.data.fields.map((field: ConnectorField) => {
        const isSet = Boolean(configQuery.data?.values[`${field.key}_set`])
        return (
          <label key={field.key} className="block space-y-1">
            <span className="text-xs font-medium text-foreground">{field.label}</span>
            <Input
              type={field.type === 'password' ? 'password' : 'text'}
              placeholder={
                field.secret && isSet
                  ? 'Leave blank to keep existing secret'
                  : field.placeholder
              }
              value={draft[field.key] ?? ''}
              onChange={(e) => setDraft((prev) => ({ ...prev, [field.key]: e.target.value }))}
            />
          </label>
        )
      })}
      <Button size="sm" disabled={saveMutation.isPending} onClick={() => void handleSave()}>
        {saveMutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Save className="h-4 w-4" />
        )}
        Save connector
      </Button>
    </div>
  )
}
