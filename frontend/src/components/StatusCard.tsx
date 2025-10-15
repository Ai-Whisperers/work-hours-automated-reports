import React from 'react'

interface StatusCardProps {
  title: string
  value: string
  icon: React.ReactNode
  status?: 'success' | 'error' | 'warning'
}

export default function StatusCard({
  title,
  value,
  icon,
  status = 'success',
}: StatusCardProps) {
  const statusColors = {
    success: 'border-green-500/50 bg-green-900/20',
    error: 'border-red-500/50 bg-red-900/20',
    warning: 'border-yellow-500/50 bg-yellow-900/20',
  }

  const iconColors = {
    success: 'text-green-400',
    error: 'text-red-400',
    warning: 'text-yellow-400',
  }

  return (
    <div
      className={`p-6 rounded-lg border ${statusColors[status]} backdrop-blur-sm`}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        <div className={iconColors[status]}>{icon}</div>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}
