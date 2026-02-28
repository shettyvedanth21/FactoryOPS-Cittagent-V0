interface ParameterRowProps {
  name: string
  value: number
  unit?: string
  timestamp?: string
}

function formatValue(val: number): string {
  return typeof val === 'number' && !Number.isInteger(val) 
    ? val.toFixed(2) 
    : String(val)
}

export function ParameterRow({ name, value, unit, timestamp }: ParameterRowProps) {
  return (
    <tr className="hover:bg-slate-800/50">
      <td className="p-3 text-white capitalize">{name}</td>
      <td className="p-3 text-white font-mono">
        {formatValue(value)}
        {unit && <span className="text-slate-400 ml-1">{unit}</span>}
      </td>
      <td className="p-3 text-slate-400">{timestamp || '--'}</td>
    </tr>
  )
}
