import { Card, CardContent } from '@/components/ui/card'
import { Device } from '@/lib/types'
import { StatusBadge } from './StatusBadge'
import { HealthScoreBadge } from './HealthScoreBadge'
import { useRouter } from 'next/navigation'

function relativeTime(ts?: string): string {
  if (!ts) return 'Never'
  
  const now = new Date()
  const then = new Date(ts)
  const diffMs = now.getTime() - then.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  
  if (diffSec < 60) return 'Just now'
  if (diffMin < 60) return `${diffMin} min ago`
  if (diffHour < 24) return `${diffHour}h ago`
  if (diffDay < 30) return `${diffDay}d ago`
  return `>30d ago`
}

interface MachineCardProps {
  device: Device
}

export function MachineCard({ device }: MachineCardProps) {
  const router = useRouter()
  
  return (
    <Card 
      className="bg-slate-800 border-slate-700 hover:shadow-lg hover:border-slate-600 transition-all cursor-pointer"
      onClick={() => router.push(`/machines/${device.device_id}`)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-bold text-white text-lg">{device.device_name}</h3>
          <StatusBadge status={device.status} />
        </div>
        
        <div className="mb-2">
          <span className="text-slate-300 capitalize">{device.device_type}</span>
          {device.location && (
            <span className="text-slate-500 ml-2">• {device.location}</span>
          )}
        </div>
        
        <div className="flex items-center gap-3 mb-3">
          {device.health_score !== undefined ? (
            <>
              <HealthScoreBadge score={device.health_score} grade={device.health_grade || 'N/A'} />
              <span className="text-sm text-slate-400">Health Score</span>
            </>
          ) : (
            <span className="text-sm text-slate-500">No health data</span>
          )}
        </div>
        
        <div className="text-xs text-slate-500">
          Last seen: {relativeTime(device.last_seen_timestamp)}
        </div>
        
        {(device.manufacturer || device.model) && (
          <div className="text-xs text-slate-600 mt-1">
            {[device.manufacturer, device.model].filter(Boolean).join(' - ')}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
