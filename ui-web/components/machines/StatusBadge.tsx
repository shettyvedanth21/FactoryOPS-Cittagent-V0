import { Badge } from '@/components/ui/badge'

interface StatusBadgeProps {
  status: 'running' | 'stopped' | 'error' | 'maintenance'
}

const statusStyles: Record<StatusBadgeProps['status'], string> = {
  running: 'bg-green-500 text-white',
  stopped: 'bg-gray-500 text-white',
  error: 'bg-red-500 text-white',
  maintenance: 'bg-amber-500 text-white',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge className={statusStyles[status]}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  )
}
