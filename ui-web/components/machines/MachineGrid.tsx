import { Device } from '@/lib/types'
import { MachineCard } from './MachineCard'
import { Skeleton } from '@/components/ui/skeleton'

interface MachineGridProps {
  devices: Device[]
  loading: boolean
}

export function MachineGrid({ devices, loading }: MachineGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <Skeleton className="h-6 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/2 mb-3" />
            <Skeleton className="h-16 w-16 rounded-full mb-3" />
            <Skeleton className="h-3 w-full" />
          </div>
        ))}
      </div>
    )
  }

  if (devices.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-slate-500 text-lg">No machines found</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {devices.map((device) => (
        <MachineCard key={device.device_id} device={device} />
      ))}
    </div>
  )
}
