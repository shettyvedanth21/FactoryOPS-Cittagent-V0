'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Server, Database, Radio, HardDrive, Activity, Loader2 } from 'lucide-react'

const SERVICES = [
  { name: 'Device Service', port: 8000, env: 'NEXT_PUBLIC_DEVICE_SERVICE_URL', description: 'Device registry and health management' },
  { name: 'Data Service', port: 8081, env: 'NEXT_PUBLIC_DATA_SERVICE_URL', description: 'Telemetry ingestion and WebSocket streaming' },
  { name: 'Rule Engine', port: 8002, env: 'NEXT_PUBLIC_RULE_ENGINE_URL', description: 'Alert rules and notification dispatch' },
  { name: 'Analytics Service', port: 8003, env: 'NEXT_PUBLIC_ANALYTICS_SERVICE_URL', description: 'ML anomaly detection and failure prediction' },
  { name: 'Reporting Service', port: 8085, env: 'NEXT_PUBLIC_REPORTING_SERVICE_URL', description: 'Energy reports and wastage analysis' },
  { name: 'Data Export Service', port: 8080, env: 'NEXT_PUBLIC_DATA_EXPORT_URL', description: 'CSV and Parquet data export' },
]

export default function SettingsPage() {
  const [serviceStatuses, setServiceStatuses] = useState<Record<string, 'checking' | 'online' | 'offline'>>({})

  useEffect(() => {
    async function checkServices() {
      for (const service of SERVICES) {
        setServiceStatuses(prev => ({ ...prev, [service.name]: 'checking' }))
        
        const url = process.env[service.env as keyof typeof process.env]
        if (!url) {
          setServiceStatuses(prev => ({ ...prev, [service.name]: 'offline' }))
          continue
        }
        
        try {
          const response = await fetch(`${url}/health`, { method: 'GET' })
          const status = response.ok ? 'online' : 'offline'
          setServiceStatuses(prev => ({ ...prev, [service.name]: status }))
        } catch {
          setServiceStatuses(prev => ({ ...prev, [service.name]: 'offline' }))
        }
      }
    }
    checkServices()
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Settings</h1>
      <p className="text-muted-foreground mb-6">System configuration and service status</p>

      <Card>
        <CardHeader>
          <CardTitle>Backend Services</CardTitle>
          <CardDescription>Connection status for all microservices</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {SERVICES.map(service => (
              <div key={service.name} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    <span className="font-medium">{service.name}</span>
                  </div>
                  <Badge
                    className={
                      serviceStatuses[service.name] === 'online'
                        ? 'bg-green-100 text-green-800 border-green-200'
                        : serviceStatuses[service.name] === 'offline'
                        ? 'bg-red-100 text-red-800 border-red-200'
                        : 'bg-gray-100 text-gray-800 border-gray-200'
                    }
                  >
                    {serviceStatuses[service.name] === 'checking' && (
                      <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    )}
                    {serviceStatuses[service.name] === 'online'
                      ? 'Online'
                      : serviceStatuses[service.name] === 'offline'
                      ? 'Offline'
                      : 'Checking...'}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{service.description}</p>
                <p className="text-xs text-muted-foreground mt-1">Port: {service.port}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Infrastructure Components</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="border rounded-lg p-4 flex items-center gap-3">
              <Database className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">MySQL</p>
                <p className="text-sm text-muted-foreground">Port: 3306</p>
              </div>
              <Badge className="ml-auto bg-gray-100 text-gray-800">Managed via Docker Compose</Badge>
            </div>
            <div className="border rounded-lg p-4 flex items-center gap-3">
              <Database className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">InfluxDB</p>
                <p className="text-sm text-muted-foreground">Port: 8086</p>
              </div>
              <Badge className="ml-auto bg-gray-100 text-gray-800">Managed via Docker Compose</Badge>
            </div>
            <div className="border rounded-lg p-4 flex items-center gap-3">
              <HardDrive className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Redis</p>
                <p className="text-sm text-muted-foreground">Port: 6379</p>
              </div>
              <Badge className="ml-auto bg-gray-100 text-gray-800">Managed via Docker Compose</Badge>
            </div>
            <div className="border rounded-lg p-4 flex items-center gap-3">
              <Radio className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">EMQX MQTT</p>
                <p className="text-sm text-muted-foreground">Port: 1883</p>
              </div>
              <Badge className="ml-auto bg-gray-100 text-gray-800">Managed via Docker Compose</Badge>
            </div>
            <div className="border rounded-lg p-4 flex items-center gap-3 md:col-span-2">
              <HardDrive className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">MinIO</p>
                <p className="text-sm text-muted-foreground">Port: 9000</p>
              </div>
              <Badge className="ml-auto bg-gray-100 text-gray-800">Managed via Docker Compose</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>About FactoryOPS</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="font-semibold">Energy Enterprise Platform v1.0</p>
          <p className="text-sm text-muted-foreground mb-4">Industrial IoT monitoring and analytics system</p>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Frontend:</span> Next.js 16 + React 19
            </div>
            <div>
              <span className="text-muted-foreground">UI:</span> shadcn/ui + Tailwind CSS
            </div>
            <div>
              <span className="text-muted-foreground">Charts:</span> Recharts
            </div>
            <div>
              <span className="text-muted-foreground">Runtime:</span> TypeScript strict mode
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
