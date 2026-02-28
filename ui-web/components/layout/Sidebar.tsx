'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Monitor, Bell, AlertTriangle, FileText, Zap, BarChart2, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getAlerts } from '@/lib/api/rules'

const navItems = [
  { href: '/machines', icon: Monitor, label: 'Machines' },
  { href: '/rules', icon: Bell, label: 'Rules' },
  { href: '/alerts', icon: AlertTriangle, label: 'Alerts', showBadge: true },
  { href: '/reports/energy', icon: FileText, label: 'Reports' },
  { href: '/wastage', icon: Zap, label: 'Wastage' },
  { href: '/analytics', icon: BarChart2, label: 'Analytics' },
  { href: '/settings', icon: Settings, label: 'Settings' },
]

export function Sidebar() {
  const pathname = usePathname()
  const [alertCount, setAlertCount] = useState(0)

  useEffect(() => {
    getAlerts({ status: 'open', limit: 1 }).then((res) => {
      if (res.success && res.pagination) {
        setAlertCount(res.pagination.total)
      }
    })
  }, [])

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-[#0f172a] text-white flex flex-col">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-2xl font-bold">FactoryOPS</h1>
      </div>
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href)
            const Icon = item.icon
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-slate-700 text-white'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                  {item.showBadge && alertCount > 0 && (
                    <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                      {alertCount > 99 ? '99+' : alertCount}
                    </span>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}
