'use client'

import React, { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getRule, deleteRule, updateRuleStatus } from '@/lib/api/rules'
import { Rule } from '@/lib/types'
import { ArrowLeft, Mail, MessageSquare, Globe, Send, MessageCircle, Loader2 } from 'lucide-react'

export default function RuleDetailPage() {
  const router = useRouter()
  const params = useParams()
  const rule_id = params.rule_id as string
  
  const [rule, setRule] = useState<Rule | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    async function fetchRule() {
      try {
        const response = await getRule(rule_id)
        if (response.success && response.data) {
          setRule(response.data)
        }
      } catch (e) {
        console.error('Failed to fetch rule', e)
      } finally {
        setLoading(false)
      }
    }
    if (rule_id) {
      fetchRule()
    }
  }, [rule_id])

  const handleDelete = async () => {
    if (!window.confirm('Delete this rule? This action cannot be undone.')) return
    setDeleting(true)
    const result = await deleteRule(rule_id)
    if (result.success) {
      router.push('/rules')
    } else {
      setDeleting(false)
      alert('Failed to delete rule')
    }
  }

  const handleToggleStatus = async () => {
    if (!rule) return
    const newStatus = rule.status === 'active' ? 'paused' : 'active'
    const result = await updateRuleStatus(rule_id, newStatus)
    if (result.success) {
      setRule({ ...rule, status: newStatus })
    }
  }

  const severityStyles: Record<string, string> = {
    info: 'bg-blue-100 text-blue-800 border-blue-200',
    warning: 'bg-amber-100 text-amber-800 border-amber-200',
    critical: 'bg-red-100 text-red-800 border-red-200',
  }

  const statusStyles: Record<string, string> = {
    active: 'bg-green-100 text-green-800 border-green-200',
    paused: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    archived: 'bg-gray-100 text-gray-800 border-gray-200',
  }

  const channelIcons: Record<string, React.ElementType> = {
    email: Mail,
    sms: MessageSquare,
    whatsapp: MessageCircle,
    telegram: Send,
    webhook: Globe,
  }

  if (loading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <Skeleton className="h-8 w-32 mb-6" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!rule) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <p>Rule not found</p>
        <Button onClick={() => router.push('/rules')} className="mt-4">
          Back to Rules
        </Button>
      </div>
    )
  }

  const notificationChannels = rule.notification_channels || {}
  const enabledChannels = Object.entries(notificationChannels).filter(
    ([_, values]) => Array.isArray(values) && values.length > 0
  )

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Button variant="ghost" onClick={() => router.push('/rules')} className="mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Rules
      </Button>

      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold">{rule.rule_name}</h1>
          {rule.description && (
            <p className="text-muted-foreground mt-1">{rule.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleToggleStatus}
            className={rule.status === 'active' 
              ? 'border-yellow-400 text-yellow-600 hover:bg-yellow-50' 
              : 'border-green-400 text-green-600 hover:bg-green-50'
            }
          >
            {rule.status === 'active' ? 'Pause' : 'Resume'}
          </Button>
          <Button
            variant="outline"
            className="border-red-400 text-red-600 hover:bg-red-50"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Delete'}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Rule Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Status</span>
              <Badge className={statusStyles[rule.status]}>{rule.status}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Severity</span>
              <Badge className={severityStyles[rule.severity]}>{rule.severity}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Trigger</span>
              <code className="text-sm bg-muted px-2 py-1 rounded">
                {rule.property} {rule.condition} {rule.threshold}
              </code>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Scope</span>
              <span>{rule.scope === 'all_devices' ? 'All Devices' : 'Selected Devices'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Cooldown</span>
              <span>{rule.cooldown_minutes} minutes</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Devices</CardTitle>
          </CardHeader>
          <CardContent>
            {rule.scope === 'all_devices' ? (
              <p className="text-muted-foreground">All devices</p>
            ) : rule.device_ids && rule.device_ids.length > 0 ? (
              <div className="space-y-1">
                {rule.device_ids.map((deviceId) => (
                  <code key={deviceId} className="block text-sm bg-muted px-2 py-1 rounded">
                    {deviceId}
                  </code>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No devices selected</p>
            )}
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Notification Channels</CardTitle>
          </CardHeader>
          <CardContent>
            {enabledChannels.length > 0 ? (
              <div className="grid gap-3 md:grid-cols-2">
                {enabledChannels.map(([channel, values]) => {
                  const IconComponent = channelIcons[channel]
                  return (
                    <div key={channel} className="flex items-center gap-3 p-3 border rounded-lg">
                      <span style={{ width: 20, height: 20 }} className="text-muted-foreground">
                        {channelIcons[channel] && React.createElement(channelIcons[channel], { size: 20 })}
                      </span>
                      <div className="flex-1">
                        <span className="font-medium capitalize">{channel}</span>
                        <p className="text-sm text-muted-foreground truncate">
                          {Array.isArray(values) ? values.join(', ') : values}
                        </p>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="text-muted-foreground">No notifications configured</p>
            )}
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Timestamps</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{new Date(rule.created_at).toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Updated</span>
              <span>{new Date(rule.updated_at).toLocaleString('en-IN')}</span>
            </div>
            {rule.last_triggered_at && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Triggered</span>
                <span>{new Date(rule.last_triggered_at).toLocaleString('en-IN')}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
