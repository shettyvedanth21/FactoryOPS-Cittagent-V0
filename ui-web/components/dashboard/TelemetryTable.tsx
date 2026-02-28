'use client'

import { useTelemetryWebSocket } from '@/lib/hooks/useTelemetryWebSocket'
import { TelemetryData } from '@/lib/types'

interface TelemetryTableProps {
  device_id: string
}

function formatTimestamp(ts: string): string {
  const date = new Date(ts)
  return date.toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  })
}

function formatValue(val: number): string {
  return typeof val === 'number' && !Number.isInteger(val) 
    ? val.toFixed(2) 
    : String(val)
}

export function TelemetryTable({ device_id }: TelemetryTableProps) {
  const { data, connected } = useTelemetryWebSocket(device_id)

  const parameters = data?.data ? Object.entries(data.data) : []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Live Telemetry</h3>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-slate-400">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {parameters.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          Waiting for data...
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-800">
              <tr>
                <th className="text-left p-3 text-slate-400 font-medium">Parameter</th>
                <th className="text-left p-3 text-slate-400 font-medium">Value</th>
                <th className="text-left p-3 text-slate-400 font-medium">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {parameters.map(([key, value]) => (
                <tr key={key} className="hover:bg-slate-800/50">
                  <td className="p-3 text-white capitalize">{key}</td>
                  <td className="p-3 text-white font-mono">{formatValue(value as number)}</td>
                  <td className="p-3 text-slate-400">{data?.timestamp ? formatTimestamp(data.timestamp) : '--'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
