'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { getDevices } from '@/lib/api/devices'
import { getWastage } from '@/lib/api/reports'
import { Device, WastageData } from '@/lib/types'
import { Zap, TrendingDown, Clock, DollarSign, Loader2 } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

const BAR_COLORS: Record<string, string> = {
  idle_running: '#f59e0b',
  peak_hour_overuse: '#ef4444',
  pressure_inefficiency: '#8b5cf6',
  other: '#6b7280',
}

function efficiencyGradeColor(grade: string): string {
  switch (grade) {
    case 'Good':
      return 'text-green-600'
    case 'Moderate':
      return 'text-amber-600'
    case 'Poor':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

export default function WastagePage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<string[]>([])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [wastageData, setWastageData] = useState<WastageData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchDevices() {
      const result = await getDevices({ limit: 100 })
      if (result.success && result.data) {
        setDevices(result.data)
      }
    }
    fetchDevices()
  }, [])

  const handleDeviceToggle = (device_id: string) => {
    setSelectedDeviceIds(prev =>
      prev.includes(device_id)
        ? prev.filter(id => id !== device_id)
        : [...prev, device_id]
    )
  }

  const handleAnalyze = async () => {
    if (selectedDeviceIds.length === 0) {
      setError('Select at least one device')
      return
    }
    if (!startDate || !endDate) {
      setError('Select date range')
      return
    }
    setError(null)
    setLoading(true)

    const result = await getWastage({
      device_ids: selectedDeviceIds.join(','),
      start_date: startDate,
      end_date: endDate,
    })

    setLoading(false)

    if (result.success && result.data) {
      setWastageData(result.data)
    } else {
      setError(result.error?.message ?? 'Failed to fetch wastage data')
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Energy Wastage Analysis</h1>
      <p className="text-muted-foreground mb-6">Identify energy waste and get actionable recommendations</p>

      <Card>
        <CardHeader>
          <CardTitle>Configure Analysis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Devices</label>
            <p className="text-sm text-muted-foreground">{selectedDeviceIds.length} selected</p>
            <div className="max-h-40 overflow-y-auto border rounded p-2 space-y-1">
              {devices.map(device => (
                <label
                  key={device.device_id}
                  className="flex items-center gap-2 p-2 hover:bg-accent rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedDeviceIds.includes(device.device_id)}
                    onChange={() => handleDeviceToggle(device.device_id)}
                    className="h-4 w-4"
                  />
                  <span className="flex-1">{device.device_name}</span>
                  <span className="text-sm text-muted-foreground">{device.device_id}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">End Date</label>
              <Input
                type="date"
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
              />
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button className="w-full" onClick={handleAnalyze} disabled={loading}>
            {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            {loading ? 'Analyzing...' : 'Analyze Wastage'}
          </Button>
        </CardContent>
      </Card>

      {wastageData && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Wasted</p>
                    <p className="text-xl font-bold">{wastageData.summary.total_wasted_kwh.toFixed(1)} <span className="text-sm font-normal">kWh</span></p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Cost Impact</p>
                    <p className="text-xl font-bold">₹{wastageData.summary.total_wasted_rupees.toLocaleString('en-IN')}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <TrendingDown className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Efficiency Score</p>
                    <p className="text-xl font-bold">{wastageData.summary.efficiency_score.toFixed(1)}%</p>
                    <p className={`text-sm ${efficiencyGradeColor(wastageData.summary.efficiency_grade)}`}>
                      {wastageData.summary.efficiency_grade}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Idle Hours</p>
                    <p className="text-xl font-bold">{wastageData.summary.idle_hours.toFixed(1)} <span className="text-sm font-normal">hrs</span></p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Wastage Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={wastageData.breakdown} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" unit=" kWh" />
                  <YAxis
                    type="category"
                    dataKey="source"
                    width={160}
                    tickFormatter={(val: string) => val.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  />
                  <Tooltip formatter={(value) => [`${Number(value).toFixed(1)} kWh`, 'Wasted']} />
                  <Bar dataKey="kwh" radius={[0, 4, 4, 0]}>
                    {wastageData.breakdown.map((entry, index) => (
                      <Cell key={index} fill={BAR_COLORS[entry.source] ?? '#6b7280'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              {wastageData.recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-3 border rounded-lg mb-3">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {rec.rank}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{rec.action}</p>
                    {rec.potential_savings_rupees && (
                      <p className="text-sm text-green-600 mt-1">
                        Potential savings: ₹{rec.potential_savings_rupees.toLocaleString('en-IN')}
                        {rec.potential_savings_kwh && ` (${rec.potential_savings_kwh.toFixed(1)} kWh)`}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Device Efficiency</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Device</TableHead>
                    <TableHead>Wasted (kWh)</TableHead>
                    <TableHead>Efficiency Score</TableHead>
                    <TableHead>Grade</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {wastageData.devices.map((device, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-mono">{device.device_id}</TableCell>
                      <TableCell>{device.wasted_kwh.toFixed(1)}</TableCell>
                      <TableCell>{device.efficiency_score.toFixed(1)}%</TableCell>
                      <TableCell>
                        <Badge
                          className={
                            device.efficiency_grade === 'Good'
                              ? 'bg-green-100 text-green-800 border-green-200'
                              : device.efficiency_grade === 'Moderate'
                              ? 'bg-amber-100 text-amber-800 border-amber-200'
                              : 'bg-red-100 text-red-800 border-red-200'
                          }
                        >
                          {device.efficiency_grade}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
