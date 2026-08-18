import React from 'react';

interface ContactSheetModalProps {
  isOpen: boolean;
  contactSheetUrl: string | null;
  campaignName: string;
  runId: string;
  onClose: () => void;
}

export const ContactSheetModal: React.FC<ContactSheetModalProps> = ({
  isOpen,
  contactSheetUrl,
  campaignName,
  runId,
  onClose,
}) => {
  if (!isOpen || !contactSheetUrl) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md p-4 animate-fade-in" onClick={onClose}>
      <div
        className="bg-[#0D151E] border border-[#1E2D3D] rounded-xl max-w-6xl w-full p-6 shadow-2xl relative overflow-hidden flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#1E2D3D]">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[#00D2FF] font-mono font-bold tracking-widest text-lg">YETI</span>
              <h2 className="text-white font-bold text-lg">Campaign Contact Sheet (18 Ads)</h2>
            </div>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              {campaignName} | Run: {runId} | 6 Audiences × 3 Ratios (1:1, 16:9, 9:16)
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <a
              href={contactSheetUrl}
              download="yeti_campaign_contact_sheet.jpg"
              className="px-4 py-2 rounded-lg bg-[#00D2FF] hover:bg-[#38bdf8] text-[#0A1118] font-bold text-xs font-mono transition-colors shadow-lg shadow-[#00D2FF]/20"
            >
              📥 Download JPG
            </a>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white bg-[#15222E] hover:bg-[#1E2D3D] rounded-lg px-3 py-2 font-mono text-xs"
            >
              Close
            </button>
          </div>
        </div>

        {/* High-res Image Scrollable Area */}
        <div className="flex-1 overflow-auto bg-[#070B0F] rounded-lg p-2 border border-[#15222E] flex justify-center items-start">
          <img
            src={contactSheetUrl}
            alt="YETI Campaign Contact Sheet"
            className="max-w-full h-auto rounded shadow-2xl"
          />
        </div>
      </div>
    </div>
  );
};
