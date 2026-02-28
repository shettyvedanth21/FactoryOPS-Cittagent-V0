'use client'

import RuleWizard from '@/components/rules/RuleWizard'
import Link from 'next/link'

export default function CreateRulePage() {
  return (
    <div>
      <div className="mb-6">
        <Link href="/rules" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to Rules
        </Link>
        <h1 className="text-2xl font-bold mt-2">Create Alert Rule</h1>
      </div>
      <RuleWizard />
    </div>
  )
}
