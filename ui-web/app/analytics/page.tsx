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
import { getDevices } from '@/lib/api/devices'
import { runAnalysis, getJob, getJobResults } from '@/lib/api/analytics'
import { Device, AnalyticsJob, AnalyticsResult } from '@/lib/types'
import { Brain, Activity, TrendingUp, Loader2 } from 'lucide-react'

function severityColor(severity: string): string {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200'
    case 'medium':
      return 'bg-amber-100 text-amber-800 border-amber-200'
    case 'low':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function riskColor(risk: string): string {
  switch (risk) {
    case 'High':
      return 'bg-red-100 text-red-800'
    case 'Medium':
      return 'bg-amber-100 text-amber-800'
    case 'Low':
      return 'bg-green-100 text-green-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export default function AnalyticsPage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [selectedDeviceId, setSelectedDeviceId] = useState('')
  const [analysisType, setAnalysisType] = useState<'anomaly_detection' | 'failure_prediction'>('anomaly_detection')
  const [sensitivity, setSensitivity] = useState<'low' | 'medium' | 'high'>('medium')
  const [lookbackDays, setLookbackDays] = useState(30)
  const [running, setRunning] = useState(false)
  const [polling, setPolling] = useState(false)
  const [currentJob, setCurrentJob] = useState<AnalyticsJob | null>(null)
  const [results, setResults] = useState<AnalyticsResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    async function fetchDevices() {
      const result = await getDevices({ limit: 100 })
      if (result.success && result.data) {
        setDevices(result.data)
      }
    }
    fetchDevices()
  }, [])

  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  const startPolling = (job_id: string) => {
    setPolling(true)
    pollingIntervalRef.current = setInterval(async () => {
      const r = await getJob(job_id)
      if (r.success && r.data) {
        setCurrentJob(r.data)
        if (r.data.status === 'completed') {
          clearInterval(pollingIntervalRef.current!)
          setPolling(false)
          fetchResults(job_id)
        } else if (r.data.status === 'failed') {
          clearInterval(pollingIntervalRef.current!)
          setPolling(false)
          setError(r.data.error_message ?? 'Analysis failed')
        }
      }
    }, 5000)
  }

  const fetchResults = async (job_id: string) => {
    const r = await getJobResults(job_id)
    if (r.success && r.data) {
      setResults(r.data)
    }
  }

  const handleRun = async () => {
    if (!selectedDeviceId) {
      setError('Select a device')
      return
    }
    setError(null)
    setRunning(true)
    setCurrentJob(null)
    setResults(null)

    const params: Record<string, unknown> = { lookback_days: lookbackDays }
    if (analysisType === 'anomaly_detection') {
      params.sensitivity = sensitivity
      params.target_parameters = ['temperature', 'vibration', 'pressure', 'power']
    }

    const result = await runAnalysis({
      device_id: selectedDeviceId,
      analysis_type: analysisType,
      parameters: params,
    })

    setRunning(false)

    if (!result.success) {
      setError(result.error?.message ?? 'Failed to start analysis')
      return
    }

    startPolling(result.data?.job_id ?? '')
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">ML Analytics</h1>
      <p className="text-muted-foreground mb-6">AI-powered anomaly detection and failure prediction</p>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Device</label>
            <Select value={selectedDeviceId} onValueChange={setSelectedDeviceId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a device" />
              </SelectTrigger>
              <SelectContent>
                {devices.map(device => (
                  <SelectItem key={device.device_id} value={device.device_id}>
                    {device.device_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            <Button
              variant={analysisType === 'anomaly_detection' ? 'default' : 'outline'}
              onClick={() => setAnalysisType('anomaly_detection')}
            >
              <Activity className="w-4 h-4 mr-2" />
              Anomaly Detection
            </Button>
            <Button
              variant={analysisType === 'failure_prediction' ? 'default' : 'outline'}
              onClick={() => setAnalysisType('failure_prediction')}
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              Failure Prediction
            </Button>
          </div>

          <p className="text-sm text-muted-foreground">
            {analysisType === 'anomaly_detection'
              ? 'Requires minimum 7 days of data. Detects unusual patterns.'
              : 'Requires minimum 30 days of data. Predicts potential failures.'}
          </p>

          <div className="grid grid-cols-2 gap-4">
            {analysisType === 'anomaly_detection' && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Sensitivity</label>
                <Select value={sensitivity} onValueChange={v => setSensitivity(v as 'low' | 'medium' | 'high')}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium">Lookback Days</label>
              <Input
                type="number"
                min={7}
                max={90}
                value={lookbackDays}
                onChange={e => setLookbackDays(parseInt(e.target.value) || 30)}
              />
            </div>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button className="w-full" onClick={handleRun} disabled={running || polling}>
            <Brain className="w-4 h-4 mr-2" />
            {running ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            {running ? 'Running...' : 'Run Analysis'}
          </Button>
        </CardContent>
      </Card>

      {currentJob && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Job Status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-mono text-sm text-muted-foreground mb-2">
              Job ID: {currentJob.job_id}
            </p>
            <div className="flex items-center gap-2 mb-4">
              {currentJob.status === 'pending' && (
                <Badge className="bg-amber-100 text-amber-800">Pending</Badge>
              )}
              {currentJob.status === 'running' && (
                <>
                  <Badge className="bg-blue-100 text-blue-800">Running</Badge>
                  <Loader2 className="w-4 h-4 animate-spin" />
                </>
              )}
              {currentJob.status === 'completed' && (
                <Badge className="bg-green-100 text-green-800">Completed</Badge>
              )}
              {currentJob.status === 'failed' && (
                <Badge className="bg-red-100 text-red-800">Failed</Badge>
              )}
            </div>
            {polling && (
              <div className="space-y-2">
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary animate-pulse w-full" />
                </div>
                <p className="text-sm text-muted-foreground">Analyzing data, this may take a few minutes...</p>
              </div>
            )}
            {currentJob.started_at && (
              <p className="text-sm text-muted-foreground">
                Started: {new Date(currentJob.started_at).toLocaleTimeString()}
              </p>
            )}
            {currentJob.completed_at && (
              <p className="text-sm text-muted-foreground">
                Completed: {new Date(currentJob.completed_at).toLocaleTimeString()}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {results && (
        <>
          {results.analysis_type === 'anomaly_detection' && (
            <>
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Analysis Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-2xl font-bold">{(results.summary as Record<string, unknown>).total_anomalies as number}</p>
                      <p className="text-sm text-muted-foreground">Total Anomalies</p>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-2 font-bold">{(results.summary as Record<string, unknown>).anomaly_rate_pct as number}%</p>
                      <p className="text-sm text-muted-foreground">Anomaly Rate</p>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-2xl font-bold">{(results.summary as Record<string, unknown>).most_affected_parameter as string}</p>
                      <p className="text-sm text-muted-foreground">Most Affected</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="mt-4">
                <CardHeader>
                  <CardTitle>Detected Anomalies</CardTitle>
                </CardHeader>
                <CardContent>
                  {results.anomalies && results.anomalies.length > 0 ? (
                    results.anomalies.map((anomaly, i) => (
                      <div key={i} className="border rounded-lg p-4 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">
                            {new Date(anomaly.timestamp).toLocaleString()}
                          </span>
                          <Badge className={severityColor(anomaly.severity)}>
                            {anomaly.severity}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium mt-1">{anomaly.context}</p>
                        <p className="text-sm text-muted-foreground mt-1">{anomaly.reasoning}</p>
                        <p className="text-sm text-blue-600 mt-2">→ {anomaly.recommended_action}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-green-600">No anomalies detected ✓</p>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {results.analysis_type === 'failure_prediction' && (
            <>
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Failure Risk Assessment</CardTitle>
                </CardHeader>
                <CardContent className="text-center py-8">
                  <Badge className={`text-lg px-4 py-2 ${riskColor((results.summary as Record<string, unknown>).failure_risk as string)}`}>
                    {(results.summary as Record<string, unknown>).failure_risk as string}
                  </Badge>
                  <p className="text-3xl font-bold mt-4">
                    {(results.summary as Record<string, unknown>).failure_probability_pct as number}% probability
                  </p>
                  <p className="text-muted-foreground mt-2">
                    Estimated remaining life: {(results.summary as Record<string, unknown>).estimated_remaining_life as string}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Confidence: {(results.summary as Record<string, unknown>).confidence_level as string}
                  </p>
                </CardContent>
              </Card>

              <Card className="mt-4">
                <CardHeader>
                  <CardTitle>Contributing Risk Factors</CardTitle>
                </CardHeader>
                <CardContent>
                  {results.risk_factors && results.risk_factors.map((risk, i) => (
                    <div key={i} className="border rounded-lg p-4 mb-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{risk.parameter}</span>
                        <Badge className="bg-red-100 text-red-800">{risk.contribution_pct}%</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">Trend: {risk.trend}</p>
                      <p className="text-sm text-muted-foreground mt-1">{risk.context}</p>
                      <p className="text-sm mt-1">{risk.reasoning}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </>
          )}

          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Recommended Actions</CardTitle>
            </CardHeader>
            <CardContent>
              {results.recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-3 border rounded mb-2">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {rec.rank}
                  </div>
                  <div>
                    <p className="font-medium">{rec.action}</p>
                    {rec.urgency && <p className="text-sm text-amber-600">{rec.urgency}</p>}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {results.data_quality && (
            <Card className="mt-4">
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">
                  Days analyzed: {(results.data_quality as Record<string, unknown>).days_analyzed as number} | 
                  Data completeness: {(results.data_quality as Record<string, unknown>).data_completeness_pct as number}%
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
