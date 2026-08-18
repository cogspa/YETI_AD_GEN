import React from 'react';
import type { GeneratedAdArtifact } from '../services/api';

interface LightboxModalProps {
  ad: GeneratedAdArtifact | null;
  onClose: () => void;
}

export const LightboxModal: React.FC<LightboxModalProps> = ({ ad, onClose }) => {
  if (!ad) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4 animate-fade-in" onClick={onClose}>
      <div
        className="bg-[#0D151E] border border-[#1E2D3D] rounded-xl max-w-4xl w-full p-6 shadow-2xl relative overflow-hidden flex flex-col md:flex-row gap-6 max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white bg-[#15222E] hover:bg-[#1E2D3D] rounded-full w-8 h-8 flex items-center justify-center font-bold z-10"
        >
          ✕
        </button>

        {/* Image Preview Container */}
        <div className="flex-1 flex items-center justify-center bg-[#070B0F] rounded-lg p-3 border border-[#15222E] overflow-hidden min-h-[300px]">
          <img
            src={ad.preview_url}
            alt={ad.filename}
            className="max-h-[70vh] max-w-full object-contain rounded drop-shadow-2xl"
          />
        </div>

        {/* Ad Details & Download Sidebar */}
        <div className="w-full md:w-80 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#00D2FF]/20 text-[#00D2FF] border border-[#00D2FF]/40">
                {ad.audience_id}
              </span>
              <span className="text-xs font-mono text-gray-400">
                {ad.aspect_ratio} ({ad.dimensions[0]}×{ad.dimensions[1]})
              </span>
            </div>

            <h3 className="text-lg font-bold text-white mb-1">{ad.audience_name}</h3>
            <p className="text-xs text-gray-400 font-mono mb-4">{ad.filename}</p>

            <div className="space-y-2 text-xs font-mono text-gray-300 bg-[#121B24] p-3 rounded-lg border border-[#1C2A38]">
              <div className="flex justify-between">
                <span className="text-gray-500">Activity:</span>
                <span className="capitalize text-[#00D2FF]">{ad.activity}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Territory:</span>
                <span>{ad.territory}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Age Band:</span>
                <span className="uppercase">{ad.age_band}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Product:</span>
                <span className="capitalize">{ad.product_color} Cooler</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">File Size:</span>
                <span>{Math.round(ad.filesize_bytes / 1024)} KB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Background:</span>
                <span className={ad.background_source === 'approved_asset' ? 'text-emerald-400' : 'text-amber-400'}>
                  {ad.background_source === 'approved_asset' ? 'Approved Asset' : 'AI Generated'}
                </span>
              </div>
            </div>

            {ad.human_review_required && (
              <div className="mt-3 p-2.5 bg-amber-950/40 border border-amber-600/50 rounded-lg text-amber-300 text-xs font-mono">
                ⚠️ <strong>Human Review Required:</strong> AI scene background variant.
              </div>
            )}
          </div>

          <div className="space-y-2 pt-4">
            <a
              href={ad.preview_url}
              download={ad.filename}
              className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-lg bg-[#00D2FF] hover:bg-[#38bdf8] text-[#0A1118] font-bold text-sm transition-colors shadow-lg shadow-[#00D2FF]/20"
            >
              <span>📥 Download PNG</span>
            </a>
            <button
              onClick={onClose}
              className="w-full py-2 rounded-lg bg-[#15222E] hover:bg-[#1E2D3D] text-gray-300 font-mono text-xs transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
