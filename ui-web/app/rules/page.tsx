'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Skeleton } from '@/components/ui/skeleton'
import { getRules, updateRuleStatus, deleteRule } from '@/lib/api/rules'
import { Rule } from '@/lib/types'
import { MoreHorizontal, Plus, AlertTriangle } from 'lucide-react'

export default function RulesPage() {
  const router = useRouter()
  const [rules, setRules] = useState<Rule[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({})

  const fetchRules = async () => {
    try {
      const response = await getRules({ limit: 100 })
      if (response.success && response.data) {
        setRules(response.data)
      }
    } catch (e) {
      console.error('Failed to fetch rules', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRules()
    const interval = setInterval(fetchRules, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleStatusChange = async (rule_id: string, status: 'active' | 'paused') => {
    setActionLoading(prev => ({ ...prev, [rule_id]: true }))
    await updateRuleStatus(rule_id, status)
    await fetchRules()
    setActionLoading(prev => ({ ...prev, [rule_id]: false }))
  }

  const handleArchive = async (rule_id: string) => {
    if (!window.confirm('Archive this rule? It will stop evaluating.')) return
    setActionLoading(prev => ({ ...prev, [rule_id]: true }))
    await deleteRule(rule_id)
    await fetchRules()
    setActionLoading(prev => ({ ...prev, [rule_id]: false }))
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

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Alert Rules</h1>
        <Button onClick={() => router.push('/rules/create')}>
          <Plus className="w-4 h-4 mr-2" />
          Create Rule
        </Button>
      </div>

      {loading ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Rule Name</TableHead>
              <TableHead>Trigger</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Devices</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[...Array(5)].map((_, i) => (
              <TableRow key={i}>
                {[...Array(7)].map((_, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : rules.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <AlertTriangle className="w-12 h-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No rules configured</h3>
          <p className="text-muted-foreground mb-4">
            Create your first rule to get started.
          </p>
          <Button onClick={() => router.push('/rules/create')}>
            <Plus className="w-4 h-4 mr-2" />
            Create Rule
          </Button>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Rule Name</TableHead>
              <TableHead>Trigger</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Devices</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rules.map((rule) => (
              <TableRow key={rule.rule_id}>
                <TableCell>
                  <span className="font-medium">{rule.rule_name}</span>
                </TableCell>
                <TableCell>
                  <code className="text-sm bg-muted px-1 rounded">
                    {rule.property} {rule.condition} {rule.threshold}
                  </code>
                </TableCell>
                <TableCell>
                  <Badge className={severityStyles[rule.severity]}>
                    {rule.severity}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge className={statusStyles[rule.status]}>
                    {rule.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {rule.scope === 'all_devices'
                    ? 'All Devices'
                    : `${rule.device_ids?.length ?? 0} device(s)`}
                </TableCell>
                <TableCell>
                  {new Date(rule.created_at).toLocaleDateString('en-IN', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                  })}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" disabled={actionLoading[rule.rule_id]}>
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {rule.status === 'active' && (
                        <DropdownMenuItem onClick={() => handleStatusChange(rule.rule_id, 'paused')}>
                          Pause Rule
                        </DropdownMenuItem>
                      )}
                      {rule.status === 'paused' && (
                        <DropdownMenuItem onClick={() => handleStatusChange(rule.rule_id, 'active')}>
                          Activate Rule
                        </DropdownMenuItem>
                      )}
                      {rule.status !== 'archived' && (
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => handleArchive(rule.rule_id)}
                        >
                          Archive Rule
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
