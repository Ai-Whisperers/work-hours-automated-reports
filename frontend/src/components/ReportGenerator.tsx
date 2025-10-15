'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { Download, Loader2, CheckCircle, XCircle, Wifi, WifiOff } from 'lucide-react'
import { generateReport, getDownloadUrl } from '@/lib/api'
import { useWebSocket } from '@/lib/useWebSocket'

export default function ReportGenerator() {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [reportFormat, setReportFormat] = useState('excel')
  const [includeUnmatched, setIncludeUnmatched] = useState(true)
  const [loading, setLoading] = useState(false)
  const [reportId, setReportId] = useState<string | null>(null)
  const [status, setStatus] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [wsUrl, setWsUrl] = useState<string | null>(null)

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket(wsUrl, {
    onMessage: (message) => {
      console.log('Received WebSocket message:', message)

      // Update status based on message type
      if (message.type === 'progress') {
        setStatus((prev: any) => ({
          ...prev,
          progress: message.progress,
          message: message.message,
        }))
      } else if (message.type === 'status') {
        setStatus((prev: any) => ({
          ...prev,
          status: message.status,
          message: message.message,
          error: message.error,
        }))

        if (message.status === 'completed' || message.status === 'failed') {
          setLoading(false)
        }
      } else if (message.type === 'completed') {
        setStatus({
          report_id: message.report_id,
          status: 'completed',
          progress: 1.0,
          message: message.message,
          download_url: message.download_url,
        })
        setLoading(false)
      }
    },
    onOpen: () => {
      console.log('WebSocket connected')
    },
    onClose: () => {
      console.log('WebSocket disconnected')
    },
  })

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    setStatus(null)

    try {
      const response = await generateReport({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        format: reportFormat,
        include_unmatched: includeUnmatched,
      })

      setReportId(response.report_id)

      // Connect to WebSocket if URL provided
      if (response.websocket_url) {
        setWsUrl(`http://localhost:8000${response.websocket_url}`)
      }

      // Initialize status
      setStatus({
        report_id: response.report_id,
        status: response.status,
        message: response.message,
        progress: 0,
      })
    } catch (err: any) {
      setLoading(false)
      setError(err.response?.data?.message || 'Failed to generate report')
    }
  }

  const handleDownload = () => {
    if (reportId) {
      window.open(getDownloadUrl(reportId), '_blank')
    }
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold">Generate Report</h2>
        {wsUrl && (
          <div className="flex items-center gap-2 text-sm">
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4 text-green-400" />
                <span className="text-green-400">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400">Disconnected</span>
              </>
            )}
          </div>
        )}
      </div>

      <form onSubmit={handleGenerateReport} className="space-y-6">
        {/* Date Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-400 mt-1">Default: 7 days ago</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-400 mt-1">Default: today</p>
          </div>
        </div>

        {/* Format Selection */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-300">
            Report Format
          </label>
          <select
            value={reportFormat}
            onChange={(e) => setReportFormat(e.target.value)}
            className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="excel">Excel (.xlsx)</option>
            <option value="html">HTML</option>
            <option value="json">JSON</option>
          </select>
        </div>

        {/* Options */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="includeUnmatched"
            checked={includeUnmatched}
            onChange={(e) => setIncludeUnmatched(e.target.checked)}
            className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-2 focus:ring-blue-500"
          />
          <label htmlFor="includeUnmatched" className="text-sm text-gray-300">
            Include unmatched time entries
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              Generate Report
            </>
          )}
        </button>
      </form>

      {/* Status Display */}
      {status && (
        <div className="mt-6 p-4 rounded-lg border border-slate-700 bg-slate-800/50">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Report Status</h3>
            {status.status === 'completed' && (
              <CheckCircle className="w-5 h-5 text-green-400" />
            )}
            {status.status === 'failed' && (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
            {status.status === 'processing' && (
              <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
            )}
          </div>

          {status.progress !== undefined && (
            <div className="mb-3">
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${status.progress * 100}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">
                {Math.round(status.progress * 100)}% complete
              </p>
            </div>
          )}

          {status.message && (
            <p className="text-sm text-gray-300 mb-2">{status.message}</p>
          )}

          {status.status === 'completed' && (
            <button
              onClick={handleDownload}
              className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              Download Report
            </button>
          )}

          {status.error && (
            <div className="mt-2 p-3 bg-red-900/20 border border-red-500/50 rounded text-sm text-red-200">
              {status.error}
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-6 p-4 bg-red-900/20 border border-red-500/50 rounded-lg flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-400 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-400">Error</h3>
            <p className="text-sm text-red-200">{error}</p>
          </div>
        </div>
      )}
    </div>
  )
}
