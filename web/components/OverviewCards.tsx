'use client'

import { 
  ChartBarIcon, 
  SignalIcon, 
  TrendingUpIcon, 
  ClockIcon 
} from '@heroicons/react/24/outline'
import { LoadingSpinner } from './LoadingSpinner'

interface OverviewCardsProps {
  signalsData?: any[]
  modelStatus?: any
  isLoading: boolean
}

export function OverviewCards({ signalsData, modelStatus, isLoading }: OverviewCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card">
            <div className="card-body">
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const totalSignals = signalsData?.length || 0
  const avgEdge = signalsData?.length > 0 
    ? (signalsData.reduce((sum, signal) => sum + signal.edge, 0) / signalsData.length).toFixed(3)
    : '0.000'
  const maxEdge = signalsData?.length > 0 
    ? Math.max(...signalsData.map(s => s.edge)).toFixed(3)
    : '0.000'
  const activeModels = modelStatus?.models?.length || 0

  const cards = [
    {
      title: 'Active Signals',
      value: totalSignals,
      icon: SignalIcon,
      color: 'text-primary-600',
      bgColor: 'bg-primary-100',
      description: 'Current analytics signals'
    },
    {
      title: 'Average Edge',
      value: `${avgEdge}`,
      icon: TrendingUpIcon,
      color: 'text-success-600',
      bgColor: 'bg-success-100',
      description: 'Average edge across signals'
    },
    {
      title: 'Max Edge',
      value: `${maxEdge}`,
      icon: ChartBarIcon,
      color: 'text-warning-600',
      bgColor: 'bg-warning-100',
      description: 'Highest edge found'
    },
    {
      title: 'Active Models',
      value: activeModels,
      icon: ClockIcon,
      color: 'text-info-600',
      bgColor: 'bg-blue-100',
      description: 'Analytics models running'
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <div key={index} className="card hover:shadow-md transition-shadow duration-200">
          <div className="card-body">
            <div className="flex items-center">
              <div className={`flex-shrink-0 p-3 rounded-lg ${card.bgColor}`}>
                <card.icon className={`h-6 w-6 ${card.color}`} />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-500">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                <p className="text-xs text-gray-500 mt-1">{card.description}</p>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
