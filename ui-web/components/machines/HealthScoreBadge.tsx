interface HealthScoreBadgeProps {
  score: number
  grade: string
  size?: 'sm' | 'lg'
}

export function HealthScoreBadge({ score, grade, size = 'sm' }: HealthScoreBadgeProps) {
  const diameter = size === 'sm' ? 60 : 120
  const radius = diameter / 2 - 4
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  
  const strokeColor = score >= 90 ? '#22c55e' : score >= 70 ? '#3b82f6' : score >= 50 ? '#eab308' : '#ef4444'
  
  const fontSize = size === 'sm' ? 14 : 28
  const labelFontSize = size === 'sm' ? 8 : 12

  return (
    <div className="flex flex-col items-center" style={{ width: diameter, height: diameter }}>
      <svg width={diameter} height={diameter} className="transform -rotate-90">
        <circle
          cx={diameter / 2}
          cy={diameter / 2}
          r={radius}
          fill="none"
          stroke="#374151"
          strokeWidth="4"
        />
        <circle
          cx={diameter / 2}
          cy={diameter / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div 
        className="absolute flex flex-col items-center justify-center"
        style={{ width: diameter, height: diameter }}
      >
        <span style={{ fontSize }} className="font-bold text-white">
          {Math.round(score)}
        </span>
        <span style={{ fontSize: labelFontSize }} className="text-gray-400">
          {grade}
        </span>
      </div>
    </div>
  )
}
