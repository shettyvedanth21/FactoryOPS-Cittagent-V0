'use client'

import { useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface RuleWizardStep3Props {
  data: {
    condition: string
    threshold: number
    severity: 'info' | 'warning' | 'critical'
    cooldown_minutes: number
  }
  onChange: (data: RuleWizardStep3Props['data']) => void
  property: string
}

const UNIT_MAP: Record<string, string> = {
  power: 'W',
  voltage: 'V',
  current: 'A',
  temperature: '°C',
  pressure: 'bar',
  humidity: '%',
  vibration: 'mm/s',
  frequency: 'Hz',
  speed: 'RPM',
  torque: 'Nm',
}

const CONDITIONS = ['>', '<', '=', '!=', '>=', '<='] as const

export function RuleWizardStep3({ data, onChange, property }: RuleWizardStep3Props) {
  const unit = UNIT_MAP[property] || ''

  const validationErrors = useMemo(() => {
    const errors: string[] = []
    if (!data.threshold && data.threshold !== 0) {
      errors.push('Threshold value is required')
    }
    if (data.cooldown_minutes < 1) {
      errors.push('Minimum 1 minute')
    }
    return errors
  }, [data.threshold, data.cooldown_minutes])

  const severityButtons = [
    { key: 'info', label: 'Info', activeClass: 'bg-blue-500 text-white', inactiveClass: 'outline' },
    { key: 'warning', label: 'Warning', activeClass: 'bg-amber-500 text-white', inactiveClass: 'outline' },
    { key: 'critical', label: 'Critical', activeClass: 'bg-red-500 text-white', inactiveClass: 'outline' },
  ] as const

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">
          Condition for: {property}
        </h3>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Condition</label>
        <div className="flex gap-2">
          {CONDITIONS.map((cond) => (
            <Button
              key={cond}
              variant={data.condition === cond ? 'default' : 'outline'}
              onClick={() => onChange({ ...data, condition: cond })}
              className="w-12"
            >
              {cond}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Threshold</label>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            placeholder="Enter threshold value"
            value={data.threshold || ''}
            onChange={(e) =>
              onChange({ ...data, threshold: parseFloat(e.target.value) || 0 })
            }
            className="max-w-xs"
          />
          {unit && <span className="text-muted-foreground">{unit}</span>}
        </div>
      </div>

      <div className="p-4 bg-muted rounded-md">
        <p className="text-sm">
          Alert when {property} {data.condition} {data.threshold} {unit}
        </p>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Severity</label>
        <div className="flex gap-2">
          {severityButtons.map(({ key, label, activeClass }) => (
            <Button
              key={key}
              variant={data.severity === key ? (key as 'default') : 'outline'}
              className={data.severity === key ? activeClass : ''}
              onClick={() => onChange({ ...data, severity: key })}
            >
              {label}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Cooldown (minutes)</label>
        <Input
          type="number"
          min={1}
          value={data.cooldown_minutes}
          onChange={(e) =>
            onChange({ ...data, cooldown_minutes: parseInt(e.target.value) || 1 })
          }
          className="max-w-xs"
        />
        <p className="text-xs text-muted-foreground">
          Minimum time between repeated alerts for same device
        </p>
      </div>

      {validationErrors.length > 0 && (
        <div className="space-y-1">
          {validationErrors.map((error, idx) => (
            <p key={idx} className="text-sm text-red-500">
              {error}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
