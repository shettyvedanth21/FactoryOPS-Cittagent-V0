'use client'

import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { getAlerts, acknowledgeAlert, resolveAlert } from '@/lib/api/rules'
import { Alert } from '@/lib/types'
import { CheckCircle, Loader2 } from 'lucide-react'

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

function relativeTime(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime()
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return `${Math.floor(diff / 86400000)}d ago`
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [deviceSearch, setDeviceSearch] = useState('')
  const [updating, setUpdating] = useState<Record<string, boolean>>({})

  const fetchAlerts = async () => {
    try {
      const response = await getAlerts({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        device_id: deviceSearch || undefined,
        limit: 100,
      })
      if (response.success) {
        setAlerts(response.data ?? [])
      }
    } catch (e) {
      console.error('Failed to fetch alerts', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 15000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    fetchAlerts()
  }, [statusFilter, severityFilter, deviceSearch])

  const handleAck = async (alert_id: string) => {
    setUpdating(prev => ({ ...prev, [alert_id]: true }))
    const result = await acknowledgeAlert(alert_id)
    if (result.success) {
      setAlerts(prev =>
        prev.map(a =>
          a.alert_id === alert_id
            ? { ...a, status: 'acknowledged' as const }
            : a
        )
      )
    }
    setUpdating(prev => ({ ...prev, [alert_id]: false }))
  }

  const handleResolve = async (alert_id: string) => {
    setUpdating(prev => ({ ...prev, [alert_id]: true }))
    const result = await resolveAlert(alert_id)
    if (result.success) {
      setAlerts(prev =>
        prev.map(a =>
          a.alert_id === alert_id
            ? { ...a, status: 'resolved' as const }
            : a
        )
      )
    }
    setUpdating(prev => ({ ...prev, [alert_id]: false }))
  }

  const openCount = alerts.filter(a => a.status === 'open').length

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <h1 className="text-2xl font-bold">Alerts</h1>
          {openCount > 0 && (
            <Badge className="ml-3 bg-red-500 text-white">{openCount} open</Badge>
          )}
        </div>
      </div>

      <div className="flex gap-3 mb-4">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Status</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="acknowledged">Acknowledged</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
          </SelectContent>
        </Select>

        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Severity</SelectItem>
            <SelectItem value="info">Info</SelectItem>
            <SelectItem value="warning">Warning</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
          </SelectContent>
        </Select>

        <Input
          placeholder="Filter by device ID..."
          value={deviceSearch}
          onChange={(e) => setDeviceSearch(e.target.value)}
          className="w-48"
        />
      </div>

      {loading ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Device</TableHead>
              <TableHead>Property & Value</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[...Array(5)].map((_, i) => (
              <TableRow key={i}>
                {[...Array(6)].map((_, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : alerts.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
          <p className="text-lg font-medium">No alerts found</p>
          <p className="text-sm">All clear — no alerts match your filters</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Device</TableHead>
              <TableHead>Property & Value</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {alerts.map((alert) => {
              const unit = UNIT_MAP[alert.property] ?? ''
              return (
                <TableRow key={alert.alert_id}>
                  <TableCell>
                    <span className="font-mono text-sm">{alert.device_id}</span>
                  </TableCell>
                  <TableCell>
                    <span>
                      {alert.property}: <strong>{alert.actual_value}</strong> {unit}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        alert.severity === 'info'
                          ? 'bg-blue-100 text-blue-800 border border-blue-200'
                          : alert.severity === 'warning'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-red-100 text-red-800 border border-red-200'
                      }
                    >
                      {alert.severity.charAt(0).toUpperCase() + alert.severity.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        alert.status === 'open'
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : alert.status === 'acknowledged'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-green-100 text-green-800 border border-green-200'
                      }
                    >
                      {alert.status.charAt(0).toUpperCase() + alert.status.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>{relativeTime(alert.created_at)}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {alert.status === 'open' && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-amber-500 text-amber-600 hover:bg-amber-50"
                          onClick={() => handleAck(alert.alert_id)}
                          disabled={!!updating[alert.alert_id]}
                        >
                          {updating[alert.alert_id] ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            'Acknowledge'
                          )}
                        </Button>
                      )}
                      {(alert.status === 'open' || alert.status === 'acknowledged') && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-green-500 text-green-600 hover:bg-green-50"
                          onClick={() => handleResolve(alert.alert_id)}
                          disabled={!!updating[alert.alert_id]}
                        >
                          {updating[alert.alert_id] ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            'Resolve'
                          )}
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
