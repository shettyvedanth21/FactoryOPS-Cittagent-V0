'use client'

import { useState, useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { StatusBadge } from '@/components/machines/StatusBadge'
import { Device } from '@/lib/types'

interface RuleWizardStep1Props {
  data: {
    rule_name: string
    description: string
    scope: 'all_devices' | 'selected_devices'
    device_ids: string[]
  }
  onChange: (data: RuleWizardStep1Props['data']) => void
  devices: Device[]
}

export function RuleWizardStep1({ data, onChange, devices }: RuleWizardStep1Props) {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredDevices = useMemo(() => {
    if (!searchTerm) return devices
    const term = searchTerm.toLowerCase()
    return devices.filter(
      (d) =>
        d.device_id.toLowerCase().includes(term) ||
        d.device_name.toLowerCase().includes(term)
    )
  }, [devices, searchTerm])

  const handleScopeChange = (scope: 'all_devices' | 'selected_devices') => {
    onChange({
      ...data,
      scope,
      device_ids: scope === 'all_devices' ? [] : data.device_ids,
    })
  }

  const handleDeviceToggle = (device_id: string) => {
    const newIds = data.device_ids.includes(device_id)
      ? data.device_ids.filter((id) => id !== device_id)
      : [...data.device_ids, device_id]
    onChange({ ...data, device_ids: newIds })
  }

  const validationError = useMemo(() => {
    if (!data.rule_name.trim()) return 'Rule name is required'
    if (data.scope === 'selected_devices' && data.device_ids.length === 0)
      return 'Select at least one device'
    return null
  }, [data.rule_name, data.scope, data.device_ids])

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <label className="text-sm font-medium">Rule Name *</label>
        <Input
          placeholder="Enter rule name"
          value={data.rule_name}
          onChange={(e) => onChange({ ...data, rule_name: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Description</label>
        <Textarea
          placeholder="Enter rule description (optional)"
          value={data.description}
          onChange={(e) => onChange({ ...data, description: e.target.value })}
          rows={3}
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Scope</label>
        <div className="flex gap-2">
          <Button
            variant={data.scope === 'all_devices' ? 'default' : 'outline'}
            onClick={() => handleScopeChange('all_devices')}
          >
            All Devices
          </Button>
          <Button
            variant={data.scope === 'selected_devices' ? 'default' : 'outline'}
            onClick={() => handleScopeChange('selected_devices')}
          >
            Selected Devices
          </Button>
        </div>
      </div>

      {data.scope === 'selected_devices' && (
        <div className="space-y-3">
          <Input
            placeholder="Search devices..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="max-h-48 overflow-y-auto border rounded-md">
            {filteredDevices.map((device) => (
              <label
                key={device.device_id}
                className="flex items-center gap-3 p-3 hover:bg-accent cursor-pointer border-b last:border-b-0"
              >
                <input
                  type="checkbox"
                  checked={data.device_ids.includes(device.device_id)}
                  onChange={() => handleDeviceToggle(device.device_id)}
                  className="h-4 w-4"
                />
                <span className="flex-1 font-medium">{device.device_name}</span>
                <span className="text-sm text-muted-foreground">{device.device_id}</span>
                <StatusBadge status={device.status} />
              </label>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            {data.device_ids.length} device(s) selected
          </p>
        </div>
      )}

      {validationError && (
        <p className="text-sm text-red-500">{validationError}</p>
      )}
    </div>
  )
}
