'use client'

import { useEffect, useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  getDevices,
} from '@/lib/api/devices'
import {
  generateComparisonReport,
  getReport,
  getReportHistory,
  getReportDownloadUrl,
} from '@/lib/api/reports'
import { Device, EnergyReport } from '@/lib/types'
import { Download, Loader2 } from 'lucide-react'

export default function ComparisonReportsPage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<string[]>([])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [format, setFormat] = useState<'pdf' | 'csv'>('pdf')
  const [generating, setGenerating] = useState(false)
  const [polling, setPolling] = useState(false)
  const [currentReport, setCurrentReport] = useState<EnergyReport | null>(null)
  const [reportHistory, setReportHistory] = useState<EnergyReport[]>([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [devicesRes, historyRes] = await Promise.all([
          getDevices({ limit: 500 }),
          getReportHistory(),
        ])
        if (devicesRes.success && devicesRes.data) {
          setDevices(devicesRes.data)
        }
        if (historyRes.success) {
          setReportHistory(historyRes.data ?? [])
        }
      } catch (e) {
        console.error('Failed to fetch data', e)
      } finally {
        setHistoryLoading(false)
      }
    }
    fetchData()
  }, [])

  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  const handleDeviceToggle = (device_id: string) => {
    setSelectedDeviceIds(prev =>
      prev.includes(device_id)
        ? prev.filter(id => id !== device_id)
        : [...prev, device_id]
    )
  }

  const fetchReportHistory = async () => {
    const r = await getReportHistory()
    if (r.success) setReportHistory(r.data ?? [])
  }

  const startPolling = (report_id: string) => {
    setPolling(true)
    pollingIntervalRef.current = setInterval(async () => {
      const r = await getReport(report_id)
      if (r.success && r.data) {
        setCurrentReport(r.data)
        if (r.data.status === 'completed' || r.data.status === 'failed') {
          clearInterval(pollingIntervalRef.current!)
          setPolling(false)
          fetchReportHistory()
        }
      }
    }, 3000)
  }

  const handleGenerate = async () => {
    if (selectedDeviceIds.length < 2) {
      setError('Select at least 2 devices')
      return
    }
    if (!startDate || !endDate) {
      setError('Select date range')
      return
    }
    if (startDate > endDate) {
      setError('Start date must be before end date')
      return
    }
    setError(null)
    setGenerating(true)
    setCurrentReport(null)

    const result = await generateComparisonReport({
      device_ids: selectedDeviceIds,
      start_date: startDate,
      end_date: endDate,
      format: format,
    })

    if (!result.success) {
      setError(result.error?.message ?? 'Failed to start report')
      setGenerating(false)
      return
    }

    const reportId = result.data?.report_id ?? null
    setGenerating(false)
    if (reportId) {
      startPolling(reportId)
    }
  }

  const handleDownload = async (report_id: string) => {
    const r = await getReportDownloadUrl(report_id)
    if (r.success && r.data?.url) {
      window.open(r.data.url, '_blank')
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
      case 'processing':
        return <Badge className="bg-amber-100 text-amber-800 border border-amber-200">Processing...</Badge>
      case 'completed':
        return <Badge className="bg-green-100 text-green-800 border border-green-200">Completed</Badge>
      case 'failed':
        return <Badge className="bg-red-100 text-red-800 border border-red-200">Failed</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const comparisonData = currentReport?.result_json as {
    devices?: Array<{
      device_id: string
      total_kwh: number
      avg_power: number
      efficiency_score: number
      rank: number
    }>
    rankings?: Array<{
      device_id: string
      total_kwh: number
      avg_power: number
      efficiency_score: number
      rank: number
    }>
  } | undefined

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Device Comparison Report</h1>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Compare Devices</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select Devices to Compare</label>
              <p className="text-sm text-muted-foreground">{selectedDeviceIds.length} selected</p>
              <div className="max-h-48 overflow-y-auto border rounded p-2 space-y-1">
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
              <p className="text-xs text-muted-foreground">Select 2 or more devices to compare</p>
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

            <div className="space-y-2">
              <label className="text-sm font-medium">Format</label>
              <Select value={format} onValueChange={v => setFormat(v as 'pdf' | 'csv')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {selectedDeviceIds.length < 2 && (
              <p className="text-sm text-amber-600">Select at least 2 devices</p>
            )}

            {error && <p className="text-sm text-red-500">{error}</p>}

            <Button
              className="w-full"
              onClick={handleGenerate}
              disabled={generating || polling || selectedDeviceIds.length < 2}
            >
              {generating && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {generating ? 'Generating...' : 'Generate Report'}
            </Button>
          </CardContent>
        </Card>

        {currentReport && currentReport.status === 'completed' && (
          <Card>
            <CardHeader>
              <CardTitle>Comparison Results</CardTitle>
            </CardHeader>
            <CardContent>
              {comparisonData?.devices || comparisonData?.rankings ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Device</TableHead>
                      <TableHead>Total kWh</TableHead>
                      <TableHead>Avg Power (W)</TableHead>
                      <TableHead>Efficiency Score</TableHead>
                      <TableHead>Rank</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(comparisonData.devices || comparisonData.rankings || []).map((item, idx) => (
                      <TableRow key={item.device_id || idx}>
                        <TableCell className="font-mono">{item.device_id}</TableCell>
                        <TableCell>{item.total_kwh.toFixed(2)}</TableCell>
                        <TableCell>{item.avg_power.toFixed(2)}</TableCell>
                        <TableCell>{item.efficiency_score.toFixed(1)}%</TableCell>
                        <TableCell>#{item.rank}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <pre className="text-xs bg-muted p-4 rounded overflow-auto">
                  {JSON.stringify(currentReport.result_json, null, 2)}
                </pre>
              )}
              <div className="mt-4">
                <Button onClick={() => handleDownload(currentReport.report_id)}>
                  <Download className="w-4 h-4 mr-2" />
                  Download Report
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {(currentReport || polling) && (
          <Card>
            <CardHeader>
              <CardTitle>Report Status</CardTitle>
            </CardHeader>
            <CardContent>
              {polling && !currentReport ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <p className="text-sm text-muted-foreground">Starting report...</p>
                </div>
              ) : currentReport ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(currentReport.status)}
                  </div>
                  {currentReport.status === 'failed' && (
                    <p className="text-red-500">
                      {currentReport.error_message ?? 'Report generation failed'}
                    </p>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Recent Reports</CardTitle>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <Table>
                <TableBody>
                  {[...Array(3)].map((_, i) => (
                    <TableRow key={i}>
                      {[...Array(5)].map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : reportHistory.length === 0 ? (
              <p className="text-muted-foreground">No reports generated yet</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportHistory.map(report => (
                    <TableRow key={report.report_id}>
                      <TableCell className="capitalize">{report.report_type}</TableCell>
                      <TableCell className="uppercase">{report.format}</TableCell>
                      <TableCell>{getStatusBadge(report.status)}</TableCell>
                      <TableCell>
                        {new Date(report.created_at).toLocaleDateString('en-IN')}
                      </TableCell>
                      <TableCell>
                        {report.status === 'completed' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(report.report_id)}
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
