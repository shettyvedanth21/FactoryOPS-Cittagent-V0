'use client'

import { usePathname } from 'next/navigation'
import { Bell } from 'lucide-react'
import { useEffect, useState, useRef } from 'react'
import { getAlerts } from '@/lib/api/rules'
import { Alert } from '@/lib/types'

const pageTitles: Record<string, string> = {
  '/machines': 'Machines',
  '/rules': 'Rules',
  '/alerts': 'Alerts',
  '/reports/energy': 'Energy Reports',
  '/reports/comparison': 'Comparison Reports',
  '/wastage': 'Wastage',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
}

export function Header() {
  const pathname = usePathname()
  const [alertCount, setAlertCount] = useState(0)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const getTitle = () => {
    for (const [path, title] of Object.entries(pageTitles)) {
      if (pathname.startsWith(path)) return title
    }
    return 'Dashboard'
  }

  useEffect(() => {
    getAlerts({ status: 'open', limit: 5 }).then((res) => {
      if (res.success && res.data) {
        setAlerts(res.data)
        setAlertCount(res.pagination?.total || 0)
      }
    })
  }, [])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <header className="h-16 border-b bg-background flex items-center justify-between px-6">
      <h2 className="text-xl font-semibold">{getTitle()}</h2>
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="relative p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <Bell className="w-5 h-5" />
          {alertCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          )}
        </button>
        {showDropdown && (
          <div className="absolute right-0 top-12 w-80 bg-background border rounded-lg shadow-lg z-50">
            <div className="p-3 border-b font-medium">Recent Alerts</div>
            {alerts.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground">No alerts</div>
            ) : (
              <ul className="max-h-64 overflow-y-auto">
                {alerts.map((alert) => (
                  <li key={alert.alert_id} className="p-3 border-b hover:bg-accent">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-sm">{alert.device_id}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {alert.message}
                        </p>
                      </div>
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${
                          alert.severity === 'critical'
                            ? 'bg-red-100 text-red-800'
                            : alert.severity === 'warning'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
