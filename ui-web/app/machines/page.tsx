'use client'

import { useEffect, useState } from 'react'
import { getDevices } from '@/lib/api/devices'
import { getAlerts } from '@/lib/api/rules'
import { Device } from '@/lib/types'
import { MachineGrid } from '@/components/machines/MachineGrid'
import { KPICard } from '@/components/dashboard/KPICard'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Monitor, Activity, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'

const DEVICE_TYPES = [
  'all', 'compressor', 'motor', 'pump', 'hvac', 'fan', 
  'conveyor', 'chiller', 'boiler', 'generator', 'transformer', 'other'
]

export default function MachinesPage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [deviceTypeFilter, setDeviceTypeFilter] = useState('all')
  const [alertCount, setAlertCount] = useState(0)

  const fetchDevices = async () => {
    const result = await getDevices({
      search: search || undefined,
      device_type: deviceTypeFilter !== 'all' ? deviceTypeFilter : undefined,
    })
    if (result.success && result.data) {
      setDevices(result.data)
    }
    setLoading(false)
  }

  const fetchAlertCount = async () => {
    const result = await getAlerts({ status: 'open' })
    if (result.success && result.pagination) {
      setAlertCount(result.pagination.total)
    }
  }

  useEffect(() => {
    fetchDevices()
    fetchAlertCount()
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      fetchDevices()
      fetchAlertCount()
    }, 10000)
    return () => clearInterval(interval)
  }, [search, deviceTypeFilter])

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchDevices()
    }, 300)
    return () => clearTimeout(timeoutId)
  }, [search, deviceTypeFilter])

  const avgHealthScore = devices.length > 0
    ? devices.reduce((sum, d) => sum + (d.health_score || 0), 0) / devices.filter(d => d.health_score !== undefined).length
    : 0

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPICard 
          title="Total Machines" 
          value={devices.length} 
          icon={<Monitor className="w-5 h-5" />} 
        />
        <KPICard 
          title="Avg Health Score" 
          value={avgHealthScore > 0 ? Math.round(avgHealthScore) : '--'} 
          unit="%" 
          icon={<Activity className="w-5 h-5" />} 
        />
        <KPICard 
          title="Active Alerts" 
          value={alertCount} 
          icon={<AlertTriangle className={`w-5 h-5 ${alertCount > 0 ? 'text-red-400' : ''}`} />} 
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="w-full sm:w-72">
          <Input 
            placeholder="Search machines..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <div className="w-full sm:w-48">
          <Select value={deviceTypeFilter} onValueChange={setDeviceTypeFilter}>
            <SelectTrigger>
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              {DEVICE_TYPES.map((type) => (
                <SelectItem key={type} value={type}>
                  {type === 'all' ? 'All Types' : type.charAt(0).toUpperCase() + type.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button 
          variant="outline" 
          onClick={() => toast.info('Coming soon')}
        >
          Add Machine
        </Button>
      </div>

      <MachineGrid devices={devices} loading={loading} />
    </div>
  )
}
