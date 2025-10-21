'use client'

import { format } from 'date-fns'
import { SignalIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { LoadingSpinner } from './LoadingSpinner'

interface RecentSignalsProps {
  signals: any[]
  isLoading: boolean
}

export function RecentSignals({ signals, isLoading }: RecentSignalsProps) {
  if (isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Recent Analytics Signals</h3>
        </div>
        <div className="card-body">
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </div>
    )
  }

  if (!signals || signals.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Recent Analytics Signals</h3>
        </div>
        <div className="card-body">
          <div className="text-center py-8">
            <SignalIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No signals found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No analytics signals are currently available.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const getEdgeColor = (edge: number) => {
    if (edge >= 0.1) return 'text-success-600 bg-success-100'
    if (edge >= 0.05) return 'text-warning-600 bg-warning-100'
    return 'text-danger-600 bg-danger-100'
  }

  const getEdgeLabel = (edge: number) => {
    if (edge >= 0.1) return 'High'
    if (edge >= 0.05) return 'Medium'
    return 'Low'
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-medium text-gray-900">Recent Analytics Signals</h3>
        <p className="mt-1 text-sm text-gray-500">
          Latest analytics insights (educational purposes only)
        </p>
      </div>
      <div className="card-body p-0">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Market</th>
                <th>Edge</th>
                <th>Fair Odds</th>
                <th>Best Odds</th>
                <th>Confidence</th>
                <th>Created</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {signals.map((signal) => (
                <tr key={signal.id} className="hover:bg-gray-50">
                  <td>
                    <div className="flex items-center">
                      <SignalIcon className="h-4 w-4 text-gray-400 mr-2" />
                      <span className="text-sm font-medium text-gray-900">
                        {signal.market}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEdgeColor(signal.edge)}`}>
                      {signal.edge.toFixed(3)}
                    </span>
                    <div className="text-xs text-gray-500 mt-1">
                      {getEdgeLabel(signal.edge)}
                    </div>
                  </td>
                  <td>
                    <span className="text-sm text-gray-900">
                      {signal.fair_odds.toFixed(2)}
                    </span>
                  </td>
                  <td>
                    <span className="text-sm text-gray-900">
                      {signal.best_book_odds.toFixed(2)}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full" 
                          style={{ width: `${(signal.confidence || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500">
                        {((signal.confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className="text-sm text-gray-500">
                      {format(new Date(signal.created_at), 'MMM dd, HH:mm')}
                    </span>
                  </td>
                  <td>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      signal.status === 'active' 
                        ? 'bg-success-100 text-success-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {signal.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="card-footer">
        <div className="flex items-center justify-between">
          <div className="flex items-center text-sm text-gray-500">
            <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
            Educational analytics only. No betting facilitation.
          </div>
          <div className="text-sm text-gray-500">
            Showing {signals.length} signals
          </div>
        </div>
      </div>
    </div>
  )
}
