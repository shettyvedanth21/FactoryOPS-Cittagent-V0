'use client'

import { use, useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { getTelemetry, getProperties } from '@/lib/api/telemetry'
import { DeviceProperty } from '@/lib/types'
import { RefreshCw, TrendingUp, Loader2 } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const TIME_RANGES = [
  { label: '1h',  value: '1h',  hours: 1   },
  { label: '6h',  value: '6h',  hours: 6   },
  { label: '24h', value: '24h', hours: 24  },
  { label: '7d',  value: '7d',  hours: 168 },
  { label: '30d', value: '30d', hours: 720 },
]

function getAggregate(hours: number): string {
  if (hours <= 1)   return '1m'
  if (hours <= 6)   return '5m'
  if (hours <= 24)  return '15m'
  if (hours <= 168) return '1h'
  return '6h'
}

const COLORS = [
  '#3b82f6', '#ef4444', '#22c55e', '#f59e0b',
  '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16',
]

function formatTime(ts: string, hours: number): string {
  const d = new Date(ts)
  if (hours <= 24) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function SingleParamChart({
  param,
  color,
  data,
  hours,
}: {
  param: string
  color: string
  data: Record<string, unknown>[]
  hours: number
}) {
  const chartData = data.map(d => ({
    time: formatTime(d.timestamp as string, hours),
    value: typeof d[param] === 'number' ? (d[param] as number) : null,
  })).filter(d => d.value !== null)

  const values = chartData.map(d => d.value as number)
  const min = values.length ? Math.min(...values) : 0
  const max = values.length ? Math.max(...values) : 1
  const padding = (max - min) * 0.1 || 1
  const domainMin = Math.floor(min - padding)
  const domainMax = Math.ceil(max + padding)

  return (
    <Card className="mb-4">
      <CardHeader className="pb-1 pt-3 px-4">
        <CardTitle className="text-sm font-semibold capitalize" style={{ color }}>
          {param.replace(/_/g, ' ')}
          <span className="ml-2 text-xs font-normal text-muted-foreground">
            {chartData.length} points
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="px-2 pb-3">
        {chartData.length === 0 ? (
          <div className="flex items-center justify-center h-24 text-sm text-muted-foreground">
            No data for this parameter
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <LineChart
              data={chartData}
              margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#334155"
                opacity={0.3}
              />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[domainMin, domainMax]}
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={false}
                width={60}
                tickFormatter={(v: number) =>
                  v >= 1000 ? `${(v/1000).toFixed(1)}k` : v.toFixed(1)
                }
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#94a3b8', marginBottom: 2 }}
                formatter={(v) => [typeof v === 'number' ? v.toFixed(2) : v, param]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                dot={false}
                strokeWidth={2}
                connectNulls={false}
                name={param}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

export default function ChartsPage({
  params,
}: {
  params: Promise<{ device_id: string }>
}) {
  const { device_id } = use(params)

  const [selectedRange, setSelectedRange]       = useState('24h')
  const [properties, setProperties]             = useState<string[]>([])
  const [selectedParams, setSelectedParams]     = useState<string[]>([])
  const [chartData, setChartData]               = useState<Record<string, unknown>[]>([])
  const [loading, setLoading]                   = useState(false)
  const [propertiesLoading, setPropertiesLoading] = useState(true)
  const [error, setError]                       = useState<string | null>(null)
  const [lastRefreshed, setLastRefreshed]       = useState<Date | null>(null)

  useEffect(() => {
    async function fetchProperties() {
      try {
        setPropertiesLoading(true)
        const result = await getProperties(device_id)
        if (result.success && result.data) {
          const props = result.data.map((p: DeviceProperty) => p.property_name)
          setProperties(props)
          setSelectedParams(props.slice(0, 3))
        }
      } catch (err) {
        console.error('Failed to fetch properties:', err)
        setError('Failed to load device properties')
      } finally {
        setPropertiesLoading(false)
      }
    }
    fetchProperties()
  }, [device_id])

  const fetchChartData = useCallback(async () => {
    if (selectedParams.length === 0) {
      setChartData([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const rangeConfig = TIME_RANGES.find(r => r.value === selectedRange)
      const hours = rangeConfig?.hours ?? 24
      const now   = new Date()
      const start = new Date(now.getTime() - hours * 60 * 60 * 1000)

      const result = await getTelemetry(device_id, {
        start:     start.toISOString(),
        end:       now.toISOString(),
        fields:    selectedParams.join(','),
        aggregate: getAggregate(hours),
        limit:     1000,
      })

      if (result.success && result.data) {
        setChartData(result.data as unknown as Record<string, unknown>[])
      } else {
        setChartData([])
        setError(result.error?.message || 'Failed to fetch data')
      }
    } catch (err) {
      console.error('Chart fetch error:', err)
      setError('Failed to fetch telemetry data')
      setChartData([])
    } finally {
      setLoading(false)
      setLastRefreshed(new Date())
    }
  }, [device_id, selectedRange, selectedParams])

  useEffect(() => {
    if (selectedParams.length > 0) fetchChartData()
  }, [fetchChartData])

  function toggleParam(param: string) {
    setSelectedParams(prev =>
      prev.includes(param) ? prev.filter(p => p !== param) : [...prev, param]
    )
  }

  const hours = TIME_RANGES.find(r => r.value === selectedRange)?.hours ?? 24

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-muted-foreground mb-1">
            <Link href={`/machines/${device_id}`} className="hover:text-foreground">
              ← {device_id}
            </Link>
          </div>
          <h1 className="text-2xl font-bold">Historical Charts</h1>
          <Badge variant="outline" className="mt-1">{device_id}</Badge>
        </div>
        <div className="flex items-center gap-3">
          {lastRefreshed && (
            <span className="text-xs text-muted-foreground">
              Updated {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={fetchChartData} disabled={loading}>
            {loading
              ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              : <RefreshCw className="h-4 w-4 mr-2" />}
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4 pb-4">
          <div className="flex flex-col sm:flex-row gap-6">
            <div>
              <p className="text-sm font-medium mb-2">Time Range</p>
              <div className="flex gap-2">
                {TIME_RANGES.map(r => (
                  <Button
                    key={r.value}
                    variant={selectedRange === r.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedRange(r.value)}
                  >
                    {r.label}
                  </Button>
                ))}
              </div>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium mb-2">Parameters</p>
              {propertiesLoading ? (
                <div className="flex gap-2">
                  {[1,2,3].map(i => <Skeleton key={i} className="h-6 w-20" />)}
                </div>
              ) : properties.length === 0 ? (
                <p className="text-sm text-muted-foreground">No parameters available</p>
              ) : (
                <div className="flex gap-4 flex-wrap">
                  {properties.map((param, idx) => (
                    <label key={param} className="flex items-center gap-2 cursor-pointer">
                      <Checkbox
                        checked={selectedParams.includes(param)}
                        onCheckedChange={() => toggleParam(param)}
                      />
                      <span className="flex items-center gap-1.5 text-sm capitalize">
                        <span
                          className="inline-block w-2.5 h-2.5 rounded-full"
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                        {param.replace(/_/g, ' ')}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-40">
            <TrendingUp className="h-8 w-8 mb-2 text-muted-foreground opacity-40" />
            <p className="text-destructive text-sm">{error}</p>
            <Button variant="ghost" size="sm" className="mt-2" onClick={fetchChartData}>
              Try again
            </Button>
          </CardContent>
        </Card>
      ) : selectedParams.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-40 text-muted-foreground">
            <TrendingUp className="h-8 w-8 mb-2 opacity-40" />
            <p className="text-sm">Select at least one parameter above</p>
          </CardContent>
        </Card>
      ) : chartData.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-40 text-muted-foreground">
            <TrendingUp className="h-8 w-8 mb-2 opacity-40" />
            <p className="text-sm font-medium">No data for selected range</p>
            <p className="text-xs mt-1">Try a larger time range</p>
          </CardContent>
        </Card>
      ) : (
        <div>
          {selectedParams.map((param, idx) => (
            <SingleParamChart
              key={param}
              param={param}
              color={COLORS[idx % COLORS.length]}
              data={chartData}
              hours={hours}
            />
          ))}
        </div>
      )}
    </div>
  )
}
