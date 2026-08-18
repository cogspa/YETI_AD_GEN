import React, { useEffect, useState } from 'react';

interface GenerationProgressModalProps {
  isOpen: boolean;
  currentStage: string;
  progressPct: number;
  completedItems: number;
  totalItems: number;
  error?: string | null;
  onClose?: () => void;
}

const STAGES = [
  'Validating JSON',
  'Resolving controlled assets',
  'Reading repeat history',
  'Selecting six concepts',
  'Generating missing backgrounds if needed',
  'Rendering 18 adaptations',
  'Running checks',
  'Uploading to Dropbox',
  'Complete',
];

export const GenerationProgressModal: React.FC<GenerationProgressModalProps> = ({
  isOpen,
  currentStage,
  progressPct,
  completedItems,
  totalItems = 18,
  error,
  onClose,
}) => {
  if (!isOpen) return null;

  const currentStageIndex = STAGES.indexOf(currentStage);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
      <div className="bg-[#0D151E] border border-[#1E2D3D] rounded-xl max-w-lg w-full p-6 shadow-2xl relative overflow-hidden">
        {/* Top decorative gradient bar */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#00D2FF] via-[#00A3FF] to-[#FF8A00]" />

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="text-[#00D2FF] font-mono text-xl font-bold tracking-widest">YETI</span>
            <span className="text-white font-semibold text-lg">Generating 18 Ads</span>
          </div>
          {currentStage === 'Complete' && (
            <span className="text-xs bg-[#00D2FF]/20 text-[#00D2FF] border border-[#00D2FF]/40 px-2 py-1 rounded font-mono">
              READY
            </span>
          )}
        </div>

        {/* Big Progress Counter */}
        <div className="my-6 text-center">
          <div className="text-4xl font-extrabold font-mono text-white tracking-wider mb-2">
            {completedItems} <span className="text-gray-500 text-2xl font-normal">/ {totalItems}</span>
          </div>
          <p className="text-sm text-[#00D2FF] font-medium animate-pulse">
            {error ? 'Generation Encountered an Error' : currentStage}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-[#15222E] rounded-full h-3 mb-6 overflow-hidden border border-[#1E2D3D]">
          <div
            className={`h-full transition-all duration-300 ${
              error
                ? 'bg-red-500'
                : currentStage === 'Complete'
                ? 'bg-gradient-to-r from-[#00D2FF] to-[#00FF88]'
                : 'bg-gradient-to-r from-[#00A3FF] to-[#00D2FF]'
            }`}
            style={{ width: `${Math.max(5, Math.min(100, progressPct))}%` }}
          />
        </div>

        {/* Stage Steps List */}
        <div className="space-y-2 mb-6 max-h-48 overflow-y-auto pr-1">
          {STAGES.map((stg, idx) => {
            const isDone = currentStageIndex > idx || currentStage === 'Complete';
            const isCurrent = currentStage === stg;

            return (
              <div
                key={stg}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono transition-colors ${
                  isCurrent
                    ? 'bg-[#152535] text-[#00D2FF] border border-[#00D2FF]/40'
                    : isDone
                    ? 'bg-[#0E1A24] text-gray-300'
                    : 'bg-[#0A1118] text-gray-600'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span className="w-4 text-center">
                    {isDone ? '✓' : isCurrent ? '▶' : '○'}
                  </span>
                  <span>{stg}</span>
                </div>
                {isCurrent && stg === 'Rendering 18 adaptations' && (
                  <span className="text-[#FF8A00] font-bold">{completedItems}/18</span>
                )}
                {isDone && <span className="text-gray-500">Done</span>}
              </div>
            );
          })}
        </div>

        {/* Error message if present */}
        {error && (
          <div className="p-3 bg-red-950/50 border border-red-800 rounded-lg text-red-300 text-xs mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex justify-end space-x-3">
          {(currentStage === 'Complete' || error) && (
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-lg bg-[#00D2FF] hover:bg-[#38bdf8] text-[#0A1118] font-bold text-sm transition-colors shadow-lg shadow-[#00D2FF]/20"
            >
              {error ? 'Close' : 'View Generated Campaign'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
