'use client'

import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { LoadingSpinner } from './LoadingSpinner'

interface SystemStatusProps {
  healthData?: any
  modelStatus?: any
  isLoading: boolean
}

export function SystemStatus({ healthData, modelStatus, isLoading }: SystemStatusProps) {
  if (isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">System Status</h3>
        </div>
        <div className="card-body">
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </div>
    )
  }

  const isHealthy = healthData?.status === 'healthy'
  const services = healthData?.services || {}

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-medium text-gray-900">System Status</h3>
      </div>
      <div className="card-body">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Overall Status */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {isHealthy ? (
                <CheckCircleIcon className="h-8 w-8 text-success-500" />
              ) : (
                <XCircleIcon className="h-8 w-8 text-danger-500" />
              )}
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">System Status</p>
              <p className={`text-sm ${isHealthy ? 'text-success-600' : 'text-danger-600'}`}>
                {isHealthy ? 'Healthy' : 'Unhealthy'}
              </p>
            </div>
          </div>

          {/* Database */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {services.database === 'healthy' ? (
                <CheckCircleIcon className="h-6 w-6 text-success-500" />
              ) : (
                <XCircleIcon className="h-6 w-6 text-danger-500" />
              )}
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">Database</p>
              <p className={`text-sm ${services.database === 'healthy' ? 'text-success-600' : 'text-danger-600'}`}>
                {services.database === 'healthy' ? 'Connected' : 'Disconnected'}
              </p>
            </div>
          </div>

          {/* Engine */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {services.engine === 'healthy' ? (
                <CheckCircleIcon className="h-6 w-6 text-success-500" />
              ) : (
                <XCircleIcon className="h-6 w-6 text-danger-500" />
              )}
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">Engine</p>
              <p className={`text-sm ${services.engine === 'healthy' ? 'text-success-600' : 'text-danger-600'}`}>
                {services.engine === 'healthy' ? 'Running' : 'Stopped'}
              </p>
            </div>
          </div>

          {/* Providers */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {services.providers === 'healthy' ? (
                <CheckCircleIcon className="h-6 w-6 text-success-500" />
              ) : (
                <ExclamationTriangleIcon className="h-6 w-6 text-warning-500" />
              )}
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">Providers</p>
              <p className={`text-sm ${services.providers === 'healthy' ? 'text-success-600' : 'text-warning-600'}`}>
                {services.providers === 'healthy' ? 'Available' : 'Limited'}
              </p>
            </div>
          </div>
        </div>

        {/* Model Status */}
        {modelStatus && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-4">Model Status</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-primary-600">
                  {modelStatus.total_signals || 0}
                </p>
                <p className="text-sm text-gray-500">Total Signals</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-success-600">
                  {modelStatus.active_signals || 0}
                </p>
                <p className="text-sm text-gray-500">Active Signals</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-warning-600">
                  {modelStatus.models?.length || 0}
                </p>
                <p className="text-sm text-gray-500">Active Models</p>
              </div>
            </div>
          </div>
        )}

        {/* Last Updated */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center text-sm text-gray-500">
            <ClockIcon className="h-4 w-4 mr-2" />
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  )
}
