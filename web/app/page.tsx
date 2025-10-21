'use client'

import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  ChartBarIcon, 
  SignalIcon, 
  CogIcon, 
  ShieldCheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { OverviewCards } from '@/components/OverviewCards'
import { RecentSignals } from '@/components/RecentSignals'
import { SystemStatus } from '@/components/SystemStatus'
import { ComplianceBanner } from '@/components/ComplianceBanner'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { api } from '@/lib/api'

export default function Dashboard() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const { data: healthData, isLoading: healthLoading } = useQuery(
    'health',
    () => api.get('/health'),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
      retry: 3,
    }
  )

  const { data: signalsData, isLoading: signalsLoading } = useQuery(
    'signals',
    () => api.post('/v1/signals/query', {
      min_edge: 0.05,
      status: 'active',
      limit: 10
    }),
    {
      refetchInterval: 60000, // Refetch every minute
      retry: 3,
    }
  )

  const { data: modelStatus, isLoading: modelLoading } = useQuery(
    'model-status',
    () => api.get('/v1/models/status'),
    {
      refetchInterval: 300000, // Refetch every 5 minutes
      retry: 3,
    }
  )

  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChartBarIcon className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-3">
                <h1 className="text-2xl font-bold text-gray-900">
                  BetFlow Engine
                </h1>
                <p className="text-sm text-gray-500">
                  Analytics Dashboard
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-500">
                <ShieldCheckIcon className="h-4 w-4 mr-1" />
                Analytics Only
              </div>
              <div className="flex items-center text-sm text-gray-500">
                <SignalIcon className="h-4 w-4 mr-1" />
                {healthData?.data?.status === 'healthy' ? (
                  <span className="text-success-600">System Online</span>
                ) : (
                  <span className="text-danger-600">System Offline</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Compliance Banner */}
      <ComplianceBanner />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* System Status */}
          <SystemStatus 
            healthData={healthData?.data}
            modelStatus={modelStatus?.data}
            isLoading={healthLoading || modelLoading}
          />

          {/* Overview Cards */}
          <OverviewCards 
            signalsData={signalsData?.data}
            modelStatus={modelStatus?.data}
            isLoading={signalsLoading || modelLoading}
          />

          {/* Recent Signals */}
          <RecentSignals 
            signals={signalsData?.data || []}
            isLoading={signalsLoading}
          />

          {/* Legal Notice */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-3 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-yellow-800">
                  Educational Analytics Only
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    This platform provides educational analytics and data insights only. 
                    No betting facilitation, no fund movement, no tips or recommendations. 
                    All data is for informational purposes and educational analysis.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
