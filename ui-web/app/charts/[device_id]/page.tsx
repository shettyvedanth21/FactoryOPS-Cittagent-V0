'use client'

import { use, useEffect, useState } from 'react'
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
  Legend,
  ResponsiveContainer,
} from 'recharts'

const TIME_RANGES = [
  { label: '1h', value: '1h', hours: 1 },
  { label: '6h', value: '6h', hours: 6 },
  { label: '24h', value: '24h', hours: 24 },
  { label: '7d', value: '7d', hours: 168 },
  { label: '30d', value: '30d', hours: 720 },
]

function getAggregate(hours: number): string {
  if (hours <= 1) return '1m'
  if (hours <= 6) return '5m'
  if (hours <= 24) return '15m'
  if (hours <= 168) return '1h'
  return '6h'
}

const LINE_COLORS = [
  '#3b82f6',
  '#ef4444',
  '#22c55e',
  '#f59e0b',
  '#8b5cf6',
  '#06b6d4',
  '#ec4899',
  '#84cc16',
]

export default function ChartsPage({ params }: { params: Promise<{ device_id: string }> }) {
  const { device_id } = use(params)
  const [selectedRange, setSelectedRange] = useState('24h')
  const [properties, setProperties] = useState<string[]>([])
  const [selectedParams, setSelectedParams] = useState<string[]>([])
  const [chartData, setChartData] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(false)
  const [propertiesLoading, setPropertiesLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null)

  useEffect(() => {
    async function fetchProperties() {
      try {
        const result = await getProperties(device_id)
        if (result.success && result.data) {
          const props = result.data.map((p: DeviceProperty) => p.property_name)
          setProperties(props)
          setSelectedParams(props.slice(0, 3))
        }
      } catch (e) {
        console.error('Failed to fetch properties', e)
      } finally {
        setPropertiesLoading(false)
      }
    }
    fetchProperties()
  }, [device_id])

  useEffect(() => {
    fetchData()
  }, [selectedRange, selectedParams])

  const fetchData = async () => {
    if (selectedParams.length === 0) {
      setChartData([])
      return
    }
    setLoading(true)
    setError(null)

    const range = TIME_RANGES.find(r => r.value === selectedRange) ?? TIME_RANGES[2]
    const end = new Date()
    const start = new Date(end.getTime() - range.hours * 60 * 60 * 1000)

    try {
      const result = await getTelemetry(device_id, {
        start: start.toISOString(),
        end: end.toISOString(),
        fields: selectedParams.join(','),
        aggregate: getAggregate(range.hours),
        limit: 1000,
      })

      setLoading(false)

      if (!result.success) {
        setError(result.error?.message ?? 'Failed to load telemetry')
        return
      }

      const transformed = (result.data ?? []).map((point) => {
        const d = new Date(point.timestamp)
        const time =
          range.hours <= 24
            ? d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
            : d.toLocaleDateString('en-IN', { month: '2-digit', day: '2-digit' }) +
              ' ' +
              d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })

        return {
          time,
          ...point.data,
        }
      })

      setChartData(transformed)
      setLastRefreshed(new Date())
    } catch (e) {
      setLoading(false)
      setError('Failed to load telemetry')
    }
  }

  const toggleParam = (param: string) => {
    setSelectedParams(prev =>
      prev.includes(param)
        ? prev.filter(p => p !== param)
        : [...prev, param]
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link
            href={`/machines/${device_id}`}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← {device_id}
          </Link>
          <h1 className="text-2xl font-bold">Historical Charts</h1>
          <Badge className="mt-1 font-mono">{device_id}</Badge>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {lastRefreshed && (
            <span className="text-xs text-muted-foreground">
              Updated {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <Card>
        <CardContent className="pt-4">
          <div className="flex gap-6">
            <div className="w-1/3">
              <p className="text-sm font-medium mb-2">Time Range</p>
              <div className="flex gap-1">
                {TIME_RANGES.map(range => (
                  <Button
                    key={range.value}
                    variant={selectedRange === range.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedRange(range.value)}
                  >
                    {range.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="flex-1">
              <p className="text-sm font-medium mb-2">Parameters</p>
              {propertiesLoading ? (
                <div className="space-y-2">
                  {[...Array(3)].map((_, i) => (
                    <Skeleton key={i} className="h-6 w-full" />
                  ))}
                </div>
              ) : (
                <div className="max-h-32 overflow-y-auto">
                  {properties.map((prop, idx) => (
                    <label
                      key={prop}
                      className="flex items-center gap-2 py-1 cursor-pointer"
                    >
                      <Checkbox
                        checked={selectedParams.includes(prop)}
                        onCheckedChange={() => toggleParam(prop)}
                      />
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: LINE_COLORS[idx % LINE_COLORS.length],
                        }}
                      />
                      <span className="text-sm">{prop}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Telemetry Trends</CardTitle>
          {selectedParams.length > 0 && (
            <div className="flex gap-2 mt-2">
              {selectedParams.map((param, idx) => (
                <Badge
                  key={param}
                  style={{
                    backgroundColor: LINE_COLORS[idx % LINE_COLORS.length] + '20',
                    color: LINE_COLORS[idx % LINE_COLORS.length],
                    borderColor: LINE_COLORS[idx % LINE_COLORS.length],
                  }}
                  variant="outline"
                >
                  {param}
                </Badge>
              ))}
            </div>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-80 flex items-center justify-center">
              <Loader2 className="animate-spin w-8 h-8" />
              <span className="ml-2">Loading chart data...</span>
            </div>
          ) : error ? (
            <div className="h-80 flex items-center justify-center text-red-500">
              {error}
            </div>
          ) : chartData.length === 0 ? (
            <div className="h-80 flex flex-col items-center justify-center text-muted-foreground">
              <TrendingUp className="w-12 h-12 mb-3" />
              <p>No data available for selected range</p>
              <p className="text-sm">Try a larger time range or check device connectivity</p>
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 11 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  {selectedParams.map((param, index) => (
                    <Line
                      key={param}
                      type="monotone"
                      dataKey={param}
                      stroke={LINE_COLORS[index % LINE_COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
              <p className="text-xs text-muted-foreground text-right mt-2">
                {chartData.length} data points
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
