'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getDevice, getShifts, createShift, deleteShift, getHealthConfigs, createHealthConfig, getUptime } from '@/lib/api/devices'
import { getAlerts } from '@/lib/api/rules'
import { getLatestTelemetry } from '@/lib/api/telemetry'
import { Device, Alert, DeviceShift, ParameterHealthConfig, TelemetryData } from '@/lib/types'
import { StatusBadge } from '@/components/machines/StatusBadge'
import { HealthScoreBadge } from '@/components/machines/HealthScoreBadge'
import { KPICard } from '@/components/dashboard/KPICard'
import { TelemetryTable } from '@/components/dashboard/TelemetryTable'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Plus, Trash2, Zap, Thermometer, Gauge } from 'lucide-react'

function relativeTime(ts?: string): string {
  if (!ts) return 'Never'
  const now = new Date()
  const then = new Date(ts)
  const diffMs = now.getTime() - then.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  
  if (diffSec < 60) return 'Just now'
  if (diffMin < 60) return `${diffMin} min ago`
  if (diffHour < 24) return `${diffHour}h ago`
  return `>24h ago`
}

export default function MachineDetailPage() {
  const params = useParams()
  const router = useRouter()
  const device_id = params.device_id as string

  const [device, setDevice] = useState<Device | null>(null)
  const [latestTelemetry, setLatestTelemetry] = useState<TelemetryData | null>(null)
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([])
  const [uptimeData, setUptimeData] = useState<unknown>(null)
  const [shifts, setShifts] = useState<DeviceShift[]>([])
  const [healthConfigs, setHealthConfigs] = useState<ParameterHealthConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  const [showShiftForm, setShowShiftForm] = useState(false)
  const [shiftForm, setShiftForm] = useState({
    shift_name: '',
    shift_start: '',
    shift_end: '',
    maintenance_break_minutes: 30,
    day_of_week: '0',
  })

  const [showHealthForm, setShowHealthForm] = useState(false)
  const [healthForm, setHealthForm] = useState({
    parameter_name: '',
    normal_min: 0,
    normal_max: 100,
    max_min: 0,
    max_max: 150,
    weight: 10,
    ignore_zero_value: false,
  })

  useEffect(() => {
    if (!device_id) return
    
    const fetchData = async () => {
      setLoading(true)
      
      const [deviceRes, telemetryRes, alertsRes, uptimeRes, shiftsRes, healthRes] = await Promise.all([
        getDevice(device_id),
        getLatestTelemetry(device_id),
        getAlerts({ device_id, status: 'open', limit: 5 }),
        getUptime(device_id, { 
          start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          end_date: new Date().toISOString().split('T')[0]
        }),
        getShifts(device_id),
        getHealthConfigs(device_id),
      ])

      if (deviceRes.success && deviceRes.data) setDevice(deviceRes.data)
      if (telemetryRes.success && telemetryRes.data) setLatestTelemetry(telemetryRes.data)
      if (alertsRes.success && alertsRes.data) setRecentAlerts(alertsRes.data)
      if (uptimeRes.success) setUptimeData(uptimeRes.data)
      if (shiftsRes.success && shiftsRes.data) setShifts(shiftsRes.data)
      if (healthRes.success && healthRes.data) setHealthConfigs(healthRes.data)
      
      setLoading(false)
    }

    fetchData()
  }, [device_id])

  const handleCreateShift = async () => {
    const result = await createShift(device_id, {
      ...shiftForm,
      day_of_week: parseInt(shiftForm.day_of_week),
      is_active: true,
    })
    if (result.success) {
      const shiftsRes = await getShifts(device_id)
      if (shiftsRes.success && shiftsRes.data) setShifts(shiftsRes.data)
      setShowShiftForm(false)
      setShiftForm({ shift_name: '', shift_start: '', shift_end: '', maintenance_break_minutes: 30, day_of_week: '0' })
    }
  }

  const handleDeleteShift = async (shiftId: number) => {
    const result = await deleteShift(device_id, shiftId)
    if (result.success) {
      setShifts(shifts.filter(s => s.id !== shiftId))
    }
  }

  const handleCreateHealthConfig = async () => {
    const result = await createHealthConfig(device_id, {
      ...healthForm,
      is_active: true,
    })
    if (result.success) {
      const healthRes = await getHealthConfigs(device_id)
      if (healthRes.success && healthRes.data) setHealthConfigs(healthRes.data)
      setShowHealthForm(false)
      setHealthForm({ parameter_name: '', normal_min: 0, normal_max: 100, max_min: 0, max_max: 150, weight: 10, ignore_zero_value: false })
    }
  }

  const totalWeight = healthConfigs.reduce((sum, c) => sum + c.weight, 0)

  if (loading) {
    return <div className="p-6">Loading...</div>
  }

  if (!device) {
    return <div className="p-6">Device not found</div>
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => router.push('/machines')} className="mb-4">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Machines
      </Button>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="telemetry">Telemetry</TabsTrigger>
          <TabsTrigger value="charts">Charts</TabsTrigger>
          <TabsTrigger value="config">Config</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white text-xl">{device.device_name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Type</span>
                    <span className="text-white capitalize">{device.device_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Location</span>
                    <span className="text-white">{device.location || '--'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Manufacturer</span>
                    <span className="text-white">{device.manufacturer || '--'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Model</span>
                    <span className="text-white">{device.model || '--'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Status</span>
                    <StatusBadge status={device.status} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Last Seen</span>
                    <span className="text-white">{relativeTime(device.last_seen_timestamp)}</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Health Score</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center">
                  <HealthScoreBadge 
                    score={device.health_score || 0} 
                    grade={device.health_grade || 'N/A'} 
                    size="lg" 
                  />
                  <p className="text-slate-400 mt-2">
                    Score: {device.health_score?.toFixed(1) || '--'}/100
                  </p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => setActiveTab('config')}
                  >
                    Configure Parameters
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <KPICard 
                  title="Power" 
                  value={latestTelemetry?.data?.power ?? '--'} 
                  unit="W"
                  icon={<Zap className="w-5 h-5" />}
                />
                <KPICard 
                  title="Voltage" 
                  value={latestTelemetry?.data?.voltage ?? '--'} 
                  unit="V"
                  icon={<Gauge className="w-5 h-5" />}
                />
                <KPICard 
                  title="Temperature" 
                  value={latestTelemetry?.data?.temperature ?? '--'} 
                  unit="°C"
                  icon={<Thermometer className="w-5 h-5" />}
                />
              </div>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Uptime</CardTitle>
                </CardHeader>
                <CardContent>
                  {shifts.length === 0 ? (
                    <p className="text-slate-500">Configure shifts to track uptime</p>
                  ) : (
                    <div className="text-center">
                      <span className="text-4xl font-bold text-white">
                        {uptimeData && typeof uptimeData === 'object' && 'uptime_percentage' in uptimeData 
                          ? (uptimeData as { uptime_percentage: number }).uptime_percentage.toFixed(1)
                          : '--'}%
                      </span>
                      <p className="text-slate-400 mt-1">Last 30 days</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Recent Alerts</CardTitle>
                </CardHeader>
                <CardContent>
                  {recentAlerts.length === 0 ? (
                    <p className="text-green-500">No active alerts ✓</p>
                  ) : (
                    <ul className="space-y-2">
                      {recentAlerts.map(alert => (
                        <li key={alert.alert_id} className="flex items-start justify-between p-2 bg-slate-700/50 rounded">
                          <div>
                            <Badge variant={alert.severity === 'critical' ? 'destructive' : 'outline'}>
                              {alert.severity}
                            </Badge>
                            <p className="text-white text-sm mt-1">{alert.message}</p>
                            <p className="text-slate-500 text-xs">{relativeTime(alert.created_at)}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="telemetry">
          <TelemetryTable device_id={device_id} />
        </TabsContent>

        <TabsContent value="charts">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Historical Charts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-slate-400">View detailed parameter trends over time</p>
              <Button onClick={() => router.push(`/charts/${device_id}`)}>
                Open Charts
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="config">
          <div className="space-y-8">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Shift Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                {shifts.length > 0 && (
                  <table className="w-full mb-4">
                    <thead>
                      <tr className="text-left text-slate-400">
                        <th className="p-2">Name</th>
                        <th className="p-2">Start</th>
                        <th className="p-2">End</th>
                        <th className="p-2">Break (min)</th>
                        <th className="p-2">Day</th>
                        <th className="p-2">Active</th>
                        <th className="p-2">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shifts.map(shift => (
                        <tr key={shift.id} className="border-t border-slate-700">
                          <td className="p-2 text-white">{shift.shift_name}</td>
                          <td className="p-2 text-white">{shift.shift_start}</td>
                          <td className="p-2 text-white">{shift.shift_end}</td>
                          <td className="p-2 text-white">{shift.maintenance_break_minutes}</td>
                          <td className="p-2 text-white">{shift.day_of_week === 0 ? 'All' : shift.day_of_week}</td>
                          <td className="p-2 text-white">{shift.is_active ? 'Yes' : 'No'}</td>
                          <td className="p-2">
                            <Button variant="destructive" size="sm" onClick={() => handleDeleteShift(shift.id)}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {showShiftForm ? (
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-4 p-4 bg-slate-700/50 rounded">
                    <Input placeholder="Shift Name" value={shiftForm.shift_name} onChange={e => setShiftForm({...shiftForm, shift_name: e.target.value})} />
                    <Input type="time" value={shiftForm.shift_start} onChange={e => setShiftForm({...shiftForm, shift_start: e.target.value})} />
                    <Input type="time" value={shiftForm.shift_end} onChange={e => setShiftForm({...shiftForm, shift_end: e.target.value})} />
                    <Input type="number" placeholder="Break (min)" value={shiftForm.maintenance_break_minutes} onChange={e => setShiftForm({...shiftForm, maintenance_break_minutes: parseInt(e.target.value)})} />
                    <Select value={shiftForm.day_of_week} onValueChange={v => setShiftForm({...shiftForm, day_of_week: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0">All Days</SelectItem>
                        {[1,2,3,4,5,6,7].map(d => <SelectItem key={d} value={String(d)}>Day {d}</SelectItem>)}
                      </SelectContent>
                    </Select>
                    <div className="flex gap-2">
                      <Button onClick={handleCreateShift}>Save</Button>
                      <Button variant="outline" onClick={() => setShowShiftForm(false)}>Cancel</Button>
                    </div>
                  </div>
                ) : (
                  <Button onClick={() => setShowShiftForm(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Shift
                  </Button>
                )}
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center justify-between">
                  Health Parameter Configuration
                  <span className={`text-sm ${Math.abs(totalWeight - 100) < 0.01 ? 'text-green-500' : 'text-red-500'}`}>
                    Total weight: {totalWeight.toFixed(1)}%
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {healthConfigs.length > 0 && (
                  <table className="w-full mb-4">
                    <thead>
                      <tr className="text-left text-slate-400">
                        <th className="p-2">Parameter</th>
                        <th className="p-2">Normal Min</th>
                        <th className="p-2">Normal Max</th>
                        <th className="p-2">Max Min</th>
                        <th className="p-2">Max Max</th>
                        <th className="p-2">Weight</th>
                        <th className="p-2">Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {healthConfigs.map(config => (
                        <tr key={config.id} className="border-t border-slate-700">
                          <td className="p-2 text-white">{config.parameter_name}</td>
                          <td className="p-2 text-white">{config.normal_min}</td>
                          <td className="p-2 text-white">{config.normal_max}</td>
                          <td className="p-2 text-white">{config.max_min}</td>
                          <td className="p-2 text-white">{config.max_max}</td>
                          <td className="p-2 text-white">{config.weight}</td>
                          <td className="p-2 text-white">{config.is_active ? 'Yes' : 'No'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {showHealthForm ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-700/50 rounded">
                    <Input placeholder="Parameter Name" value={healthForm.parameter_name} onChange={e => setHealthForm({...healthForm, parameter_name: e.target.value})} />
                    <Input type="number" placeholder="Normal Min" value={healthForm.normal_min} onChange={e => setHealthForm({...healthForm, normal_min: parseFloat(e.target.value)})} />
                    <Input type="number" placeholder="Normal Max" value={healthForm.normal_max} onChange={e => setHealthForm({...healthForm, normal_max: parseFloat(e.target.value)})} />
                    <Input type="number" placeholder="Max Min" value={healthForm.max_min} onChange={e => setHealthForm({...healthForm, max_min: parseFloat(e.target.value)})} />
                    <Input type="number" placeholder="Max Max" value={healthForm.max_max} onChange={e => setHealthForm({...healthForm, max_max: parseFloat(e.target.value)})} />
                    <Input type="number" placeholder="Weight" value={healthForm.weight} onChange={e => setHealthForm({...healthForm, weight: parseFloat(e.target.value)})} />
                    <div className="flex items-center gap-2">
                      <input type="checkbox" checked={healthForm.ignore_zero_value} onChange={e => setHealthForm({...healthForm, ignore_zero_value: e.target.checked})} />
                      <span className="text-white">Ignore Zero</span>
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleCreateHealthConfig}>Save</Button>
                      <Button variant="outline" onClick={() => setShowHealthForm(false)}>Cancel</Button>
                    </div>
                  </div>
                ) : (
                  <Button onClick={() => setShowHealthForm(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Parameter
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
