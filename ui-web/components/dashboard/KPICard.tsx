import { Card, CardContent } from '@/components/ui/card'
import { ReactNode } from 'react'

interface KPICardProps {
  title: string
  value: string | number
  unit?: string
  icon?: ReactNode
  subtitle?: string
}

export function KPICard({ title, value, unit, icon, subtitle }: KPICardProps) {
  return (
    <Card className="bg-slate-800 border-slate-700">
      <CardContent className="p-4 relative">
        {icon && (
          <div className="absolute top-4 right-4 text-slate-400">
            {icon}
          </div>
        )}
        <div className="text-sm text-slate-400">{title}</div>
        <div className="flex items-baseline gap-1 mt-2">
          <span className="text-3xl font-bold text-white">{value}</span>
          {unit && <span className="text-lg text-slate-400">{unit}</span>}
        </div>
        {subtitle && (
          <div className="text-xs text-slate-500 mt-1">{subtitle}</div>
        )}
      </CardContent>
    </Card>
  )
}
