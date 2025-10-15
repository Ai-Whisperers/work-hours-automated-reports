'use client'

import { useState, useEffect } from 'react'
import { FileText, Activity, Clock, AlertCircle } from 'lucide-react'
import ReportGenerator from '@/components/ReportGenerator'
import StatusCard from '@/components/StatusCard'
import { checkHealth, checkServices } from '@/lib/api'

export default function Home() {
  const [health, setHealth] = useState<any>(null)
  const [services, setServices] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [healthData, servicesData] = await Promise.all([
          checkHealth(),
          checkServices()
        ])
        setHealth(healthData)
        setServices(servicesData)
      } catch (error) {
        console.error('Failed to fetch status:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, [])

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
            Work Hours Automated Reports
          </h1>
          <p className="text-gray-400">
            Generate time tracking reports from Clockify and Azure DevOps
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <StatusCard
            title="API Status"
            value={loading ? '...' : health?.status || 'Unknown'}
            icon={<Activity className="w-6 h-6" />}
            status={health?.status === 'healthy' ? 'success' : 'error'}
          />
          <StatusCard
            title="Clockify"
            value={loading ? '...' : services?.clockify ? 'Connected' : 'Disconnected'}
            icon={<Clock className="w-6 h-6" />}
            status={services?.clockify ? 'success' : 'error'}
          />
          <StatusCard
            title="Azure DevOps"
            value={loading ? '...' : services?.azure_devops ? 'Connected' : 'Disconnected'}
            icon={<FileText className="w-6 h-6" />}
            status={services?.azure_devops ? 'success' : 'error'}
          />
        </div>

        {/* Alert if services are down */}
        {!loading && services && (!services.clockify || !services.azure_devops) && (
          <div className="mb-8 p-4 bg-yellow-900/20 border border-yellow-500/50 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-500">Service Connection Issue</h3>
              <p className="text-sm text-yellow-200/80">
                Some services are not connected. Please check your configuration.
              </p>
            </div>
          </div>
        )}

        {/* Report Generator */}
        <ReportGenerator />
      </div>
    </main>
  )
}
