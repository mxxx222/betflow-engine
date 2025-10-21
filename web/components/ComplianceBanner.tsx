'use client'

import { ExclamationTriangleIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'

export function ComplianceBanner() {
  return (
    <div className="bg-blue-50 border-b border-blue-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center">
          <ShieldCheckIcon className="h-5 w-5 text-blue-400 mr-3" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-blue-800">
              Legal Compliance Notice
            </h3>
            <p className="text-sm text-blue-700 mt-1">
              This platform operates in <strong>analytics-only mode</strong>. All data insights are for 
              educational purposes only. No betting facilitation, no fund movement, no tips or recommendations.
            </p>
          </div>
          <div className="ml-4">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Analytics Only
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
