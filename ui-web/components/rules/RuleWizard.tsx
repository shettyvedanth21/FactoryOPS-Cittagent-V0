'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RuleWizardStep1 } from './RuleWizardStep1_Scope'
import { RuleWizardStep2 } from './RuleWizardStep2_Property'
import { RuleWizardStep3 } from './RuleWizardStep3_Condition'
import { RuleWizardStep4 } from './RuleWizardStep4_Notify'
import { getDevices } from '@/lib/api/devices'
import { createRule } from '@/lib/api/rules'
import { Device } from '@/lib/types'

interface FormData {
  rule_name: string
  description: string
  scope: 'all_devices' | 'selected_devices'
  device_ids: string[]
  property: string
  condition: string
  threshold: number
  severity: 'info' | 'warning' | 'critical'
  cooldown_minutes: number
  notifications: {
    email: string[]
    sms: string[]
    webhook: string[]
    whatsapp: string[]
    telegram: string[]
  }
}

const STEPS = [
  { num: 1, label: 'Scope' },
  { num: 2, label: 'Property' },
  { num: 3, label: 'Condition' },
  { num: 4, label: 'Notify' },
]

function CheckCircle2Icon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <path d="m9 11 3 3L22 4" />
    </svg>
  )
}

function Loader2Icon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  )
}

export default function RuleWizard() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1)
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [stepError, setStepError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [formData, setFormData] = useState<FormData>({
    rule_name: '',
    description: '',
    scope: 'all_devices',
    device_ids: [],
    property: '',
    condition: '>',
    threshold: 0,
    severity: 'warning',
    cooldown_minutes: 15,
    notifications: {
      email: ['vedanth.shetty@cittagent.com', 'manash.ray@cittagent.com'],
      sms: [],
      webhook: [],
      whatsapp: [],
      telegram: [],
    },
  })

  useEffect(() => {
    async function fetchDevices() {
      try {
        const response = await getDevices({ limit: 100 })
        if (response.success && response.data) {
          setDevices(response.data)
        }
      } catch (e) {
        console.error('Failed to fetch devices', e)
      } finally {
        setLoading(false)
      }
    }
    fetchDevices()
  }, [])

  const validateStep = (step: number): string | null => {
    if (step === 1) {
      if (!formData.rule_name.trim()) return 'Rule name is required'
      if (formData.scope === 'selected_devices' && formData.device_ids.length === 0)
        return 'Select at least one device'
    }
    if (step === 2) {
      if (!formData.property) return 'Select a property to monitor'
    }
    if (step === 3) {
      if (formData.threshold === undefined || formData.threshold === null)
        return 'Threshold value is required'
      if (formData.cooldown_minutes < 1) return 'Minimum cooldown is 1 minute'
    }
    if (step === 4) {
      const hasEntry = Object.values(formData.notifications).some(arr => arr.length > 0)
      if (!hasEntry) return 'Add at least one notification recipient'
    }
    return null
  }

  const handleNext = () => {
    const error = validateStep(currentStep)
    if (error) {
      setStepError(error)
      return
    }
    setStepError(null)
    setCurrentStep(prev => (prev + 1) as 1 | 2 | 3 | 4)
  }

  const handleBack = () => {
    setStepError(null)
    if (currentStep === 1) {
      router.push('/rules')
    } else {
      setCurrentStep(prev => (prev - 1) as 1 | 2 | 3 | 4)
    }
  }

  const handleSubmit = async () => {
    const error = validateStep(4)
    if (error) {
      setStepError(error)
      return
    }
    setSubmitting(true)
    setSubmitError(null)
    
    const result = await createRule({
      rule_name: formData.rule_name,
      description: formData.description,
      scope: formData.scope,
      device_ids: formData.scope === 'all_devices' ? [] : formData.device_ids,
      property: formData.property,
      condition: formData.condition as '>' | '<' | '=' | '!=' | '>=' | '<=',
      threshold: formData.threshold,
      severity: formData.severity,
      cooldown_minutes: formData.cooldown_minutes,
      notification_channels: formData.notifications,
    })
    
    if (result.success) {
      router.push('/rules')
    } else {
      setSubmitError(result.error?.message ?? 'Failed to create rule')
      setSubmitting(false)
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <RuleWizardStep1
            data={{
              rule_name: formData.rule_name,
              description: formData.description,
              scope: formData.scope,
              device_ids: formData.device_ids,
            }}
            onChange={(d: Partial<FormData>) => setFormData(prev => ({ ...prev, ...d }))}
            devices={devices}
          />
        )
      case 2:
        return (
          <RuleWizardStep2
            data={{ property: formData.property }}
            onChange={(d: { property: string }) => setFormData(prev => ({ ...prev, ...d }))}
            device_ids={formData.scope === 'all_devices' ? [] : formData.device_ids}
          />
        )
      case 3:
        return (
          <RuleWizardStep3
            data={{
              condition: formData.condition,
              threshold: formData.threshold,
              severity: formData.severity,
              cooldown_minutes: formData.cooldown_minutes,
            }}
            onChange={(d: { condition: string; threshold: number; severity: 'info' | 'warning' | 'critical'; cooldown_minutes: number }) => setFormData(prev => ({ ...prev, ...d }))}
            property={formData.property}
          />
        )
      case 4:
        return (
          <RuleWizardStep4
            data={{ notifications: formData.notifications }}
            onChange={(d: { notifications: FormData['notifications'] }) => setFormData(prev => ({ ...prev, ...d }))}
            ruleSummary={{
              rule_name: formData.rule_name,
              property: formData.property,
              condition: formData.condition,
              threshold: formData.threshold,
              severity: formData.severity,
              device_count: formData.scope === 'all_devices' ? 0 : formData.device_ids.length,
            }}
          />
        )
    }
  }

  return (
    <Card className="max-w-3xl mx-auto">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          {STEPS.map((step, idx) => (
            <div key={step.num} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                    step.num < currentStep
                      ? 'bg-primary text-white'
                      : step.num === currentStep
                      ? 'bg-primary text-white'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {step.num < currentStep ? (
                    <CheckCircle2Icon />
                  ) : (
                    step.num
                  )}
                </div>
                <span className="text-xs text-center mt-1 text-muted-foreground">
                  {step.label}
                </span>
              </div>
              {idx < STEPS.length - 1 && (
                <div className="flex-1 h-px bg-border mx-2" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <p className="text-muted-foreground">Loading devices...</p>
        ) : (
          renderStep()
        )}
      </div>

      <div className="sticky bottom-0 border-t p-4 bg-background flex items-center justify-between">
        <div>
          <Button
            variant="ghost"
            onClick={handleBack}
          >
            Back
          </Button>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div>
            {currentStep < 4 ? (
              <Button variant="default" onClick={handleNext}>
                Next →
              </Button>
            ) : (
              <Button
                variant="default"
                onClick={handleSubmit}
                disabled={submitting}
              >
                {submitting && <Loader2Icon className="animate-spin mr-2" />}
                {submitting ? 'Creating...' : 'Create Rule'}
              </Button>
            )}
          </div>
          {stepError && <p className="text-sm text-red-500">{stepError}</p>}
          {submitError && <p className="text-sm text-red-500">{submitError}</p>}
        </div>
      </div>
    </Card>
  )
}
