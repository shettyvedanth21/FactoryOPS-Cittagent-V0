'use client'

import React, { useState, useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface NotificationChannels {
  email: string[]
  sms: string[]
  webhook: string[]
  whatsapp: string[]
  telegram: string[]
}

interface RuleWizardStep4Props {
  data: {
    notifications: NotificationChannels
  }
  onChange: (data: { notifications: NotificationChannels }) => void
  ruleSummary: {
    rule_name: string
    property: string
    condition: string
    threshold: number
    severity: string
    device_count: number
  }
}

interface ChannelConfig {
  key: keyof NotificationChannels
  label: string
  icon: string
  placeholder: string
}

const CHANNELS: ChannelConfig[] = [
  { key: 'email', label: 'Email', icon: 'Mail', placeholder: 'user@example.com' },
  { key: 'sms', label: 'SMS', icon: 'MessageSquare', placeholder: '+91XXXXXXXXXX' },
  { key: 'whatsapp', label: 'WhatsApp', icon: 'MessageCircle', placeholder: '+91XXXXXXXXXX' },
  { key: 'telegram', label: 'Telegram', icon: 'Send', placeholder: 'Chat ID e.g. -1001234567890' },
  { key: 'webhook', label: 'Webhook', icon: 'Globe', placeholder: 'https://hooks.example.com/...' },
]

const severityColors: Record<string, string> = {
  info: 'bg-blue-500',
  warning: 'bg-amber-500',
  critical: 'bg-red-500',
}

function MailIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="16" x="2" y="4" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  )
}

function MessageSquareIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function MessageCircleIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
    </svg>
  )
}

function SendIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </svg>
  )
}

function GlobeIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
      <path d="M2 12h20" />
    </svg>
  )
}

const ICONS: Record<string, React.ComponentType> = {
  Mail: MailIcon,
  MessageSquare: MessageSquareIcon,
  MessageCircle: MessageCircleIcon,
  Send: SendIcon,
  Globe: GlobeIcon,
}

export function RuleWizardStep4({ data, onChange, ruleSummary }: RuleWizardStep4Props) {
  const [channelInputs, setChannelInputs] = useState<Record<string, string>>({})

  const handleToggleChannel = (key: keyof NotificationChannels) => {
    const current = data.notifications[key]
    if (current && current.length > 0) {
      onChange({
        notifications: {
          ...data.notifications,
          [key]: [],
        },
      })
    } else {
      const defaultRecipients: Record<string, string[]> = {
        email: ['vedanth.shetty@cittagent.com', 'manash.ray@cittagent.com'],
        sms: [],
        whatsapp: [],
        telegram: [],
        webhook: [],
      }
      onChange({
        notifications: {
          ...data.notifications,
          [key]: defaultRecipients[key] || [],
        },
      })
    }
  }

  const handleAddEntry = (key: keyof NotificationChannels) => {
    const value = channelInputs[key]?.trim()
    if (!value) return

    const current = data.notifications[key] || []
    onChange({
      notifications: {
        ...data.notifications,
        [key]: [...current, value],
      },
    })
    setChannelInputs({ ...channelInputs, [key]: '' })
  }

  const handleRemoveEntry = (key: keyof NotificationChannels, index: number) => {
    const current = data.notifications[key]
    onChange({
      notifications: {
        ...data.notifications,
        [key]: current.filter((_, i) => i !== index),
      },
    })
  }

  const validationError = useMemo(() => {
    const hasEnabledChannel = CHANNELS.some(
      (ch) => data.notifications[ch.key] && data.notifications[ch.key].length > 0
    )
    if (!hasEnabledChannel) {
      return 'At least one channel enabled with one entry required'
    }
    return null
  }, [data.notifications])

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Rule Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm">
            <span className="font-medium">Rule:</span> {ruleSummary.rule_name}
          </p>
          <p className="text-sm">
            <span className="font-medium">Trigger:</span> {ruleSummary.property}{' '}
            {ruleSummary.condition} {ruleSummary.threshold}
          </p>
          <p className="text-sm">
            <span className="font-medium">Severity:</span>{' '}
            <Badge className={severityColors[ruleSummary.severity] || 'bg-gray-500'}>
              {ruleSummary.severity}
            </Badge>
          </p>
          <p className="text-sm">
            <span className="font-medium">Applies to:</span> {ruleSummary.device_count} device(s)
          </p>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {CHANNELS.map((channel) => {
          const IconComponent = ICONS[channel.icon]
          const isEnabled = data.notifications[channel.key]?.length > 0

          return (
            <div key={channel.key} className="space-y-2">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleToggleChannel(channel.key)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isEnabled ? 'bg-primary' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <IconComponent />
                <span className="font-medium">{channel.label}</span>
              </div>

              {isEnabled && (
                <div className="ml-9 space-y-2">
                  <div className="flex gap-2">
                    <Input
                      placeholder={channel.placeholder}
                      value={channelInputs[channel.key] || ''}
                      onChange={(e) =>
                        setChannelInputs({ ...channelInputs, [channel.key]: e.target.value })
                      }
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleAddEntry(channel.key)
                        }
                      }}
                    />
                    <Button type="button" onClick={() => handleAddEntry(channel.key)}>
                      Add
                    </Button>
                  </div>

                  {data.notifications[channel.key]?.map((entry, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between bg-muted px-3 py-2 rounded-md"
                    >
                      <span className="text-sm truncate">{entry}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveEntry(channel.key, idx)}
                        className="text-red-500 hover:text-red-700 ml-2"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M18 6 6 18" />
                          <path d="m6 6 12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {validationError && (
        <p className="text-sm text-red-500">{validationError}</p>
      )}
    </div>
  )
}
