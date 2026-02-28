'use client'

import { useEffect, useState, useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { getProperties } from '@/lib/api/telemetry'
import { DeviceProperty } from '@/lib/types'

interface RuleWizardStep2Props {
  data: { property: string }
  onChange: (data: { property: string }) => void
  device_ids: string[]
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

export function RuleWizardStep2({ data, onChange, device_ids }: RuleWizardStep2Props) {
  const [properties, setProperties] = useState<string[]>([])
  const [customProperty, setCustomProperty] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchProperties() {
      try {
        const device_id = device_ids.length === 1 ? device_ids[0] : undefined
        const response = await getProperties(device_id)
        if (response.success && response.data && response.data.length > 0) {
          const uniqueProps = [...new Set(response.data.map((p: DeviceProperty) => p.property_name))]
          setProperties(uniqueProps)
        } else {
          setProperties(Object.keys(UNIT_MAP))
        }
      } catch {
        setProperties(Object.keys(UNIT_MAP))
      } finally {
        setLoading(false)
      }
    }
    fetchProperties()
  }, [device_ids])

  const validationError = useMemo(() => {
    if (!data.property.trim()) return 'Select a property to monitor'
    return null
  }, [data.property])

  const handleCustomPropertyChange = (value: string) => {
    setCustomProperty(value)
    onChange({ property: value })
  }

  const handlePropertySelect = (property: string) => {
    setCustomProperty('')
    onChange({ property })
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Select the parameter to monitor</h3>
        {loading ? (
          <p className="text-muted-foreground">Loading properties...</p>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {properties.map((property) => (
              <Card
                key={property}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  data.property === property
                    ? 'ring-2 ring-primary border-primary'
                    : 'border'
                }`}
                onClick={() => handlePropertySelect(property)}
              >
                <CardContent className="p-4 flex flex-col items-center justify-center py-6 relative">
                  {data.property === property && (
                    <div className="absolute top-2 right-2">
                      <svg
                        className="w-5 h-5 text-primary"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  )}
                  <span className="font-semibold text-center">{property}</span>
                  <span className="text-sm text-muted-foreground">
                    {UNIT_MAP[property] || ''}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Or enter custom property name</label>
        <Input
          placeholder="Enter custom property name"
          value={customProperty}
          onChange={(e) => handleCustomPropertyChange(e.target.value)}
        />
      </div>

      {validationError && (
        <p className="text-sm text-red-500">{validationError}</p>
      )}
    </div>
  )
}
