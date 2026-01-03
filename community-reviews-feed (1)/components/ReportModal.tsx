
import React, { useState } from 'react';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (reason: string, details: string) => Promise<void>;
  targetTitle: string;
}

const REPORT_REASONS = [
  { id: 'spoiler', label: 'Unmarked Spoilers', description: 'Contains significant plot points not marked as spoilers.' },
  { id: 'harassment', label: 'Harassment or Hate Speech', description: 'Targeting individuals or groups with abusive language.' },
  { id: 'spam', label: 'Spam or Misleading', description: 'Repeated content, advertisements, or fake information.' },
  { id: 'inappropriate', label: 'Inappropriate Content', description: 'Explicit or highly offensive material.' },
  { id: 'other', label: 'Other', description: 'Something else that violates our community guidelines.' },
];

const ReportModal: React.FC<ReportModalProps> = ({ isOpen, onClose, onSubmit, targetTitle }) => {
  const [selectedReason, setSelectedReason] = useState('');
  const [details, setDetails] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReason || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onSubmit(selectedReason, details);
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        setSelectedReason('');
        setDetails('');
        onClose();
      }, 2000);
    } catch (error) {
      alert("Failed to submit report. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/70 backdrop-blur-md animate-in fade-in duration-300"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative bg-white w-full max-w-lg rounded-[2.5rem] shadow-2xl overflow-hidden animate-in zoom-in-95 fade-in duration-300">
        {isSuccess ? (
          <div className="p-12 text-center animate-in fade-in zoom-in-90 duration-300">
            <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
              <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-black text-slate-900 mb-2">Report Received</h2>
            <p className="text-slate-500 font-medium">Thank you for helping us keep MediaHub safe. Our moderators will review this shortly.</p>
          </div>
        ) : (
          <>
            <div className="px-8 pt-8 pb-4 border-b border-slate-50">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-2xl font-black text-slate-900 tracking-tighter">Report Content</h2>
                <button 
                  onClick={onClose}
                  className="p-2 rounded-full hover:bg-slate-100 text-slate-400 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-sm font-medium text-slate-400">
                You are reporting the review for <span className="text-slate-900 font-bold">"{targetTitle}"</span>.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              <div className="space-y-3">
                <label className="text-[11px] font-black text-slate-500 uppercase tracking-widest ml-1">Why are you reporting this?</label>
                <div className="space-y-2 max-h-[240px] overflow-y-auto pr-2 custom-scrollbar">
                  {REPORT_REASONS.map((reason) => (
                    <label 
                      key={reason.id}
                      className={`block p-4 rounded-2xl border-2 cursor-pointer transition-all hover:border-indigo-200 ${
                        selectedReason === reason.id 
                          ? 'border-indigo-600 bg-indigo-50/50 shadow-sm' 
                          : 'border-slate-100 bg-slate-50/30'
                      }`}
                    >
                      <div className="flex items-center">
                        <input 
                          type="radio"
                          name="reportReason"
                          className="hidden"
                          value={reason.id}
                          checked={selectedReason === reason.id}
                          onChange={(e) => setSelectedReason(e.target.value)}
                        />
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mr-4 transition-all ${
                          selectedReason === reason.id ? 'border-indigo-600 bg-indigo-600' : 'border-slate-300 bg-white'
                        }`}>
                          {selectedReason === reason.id && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                        </div>
                        <div>
                          <div className="text-sm font-black text-slate-900">{reason.label}</div>
                          <div className="text-[11px] text-slate-400 font-medium leading-tight">{reason.description}</div>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-black text-slate-500 uppercase tracking-widest ml-1">Additional Details (Optional)</label>
                <textarea 
                  placeholder="Provide more context for our moderators..."
                  className="w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-3xl text-sm text-slate-900 font-medium focus:ring-4 focus:ring-indigo-500/10 focus:bg-white outline-none transition-all resize-none min-h-[100px] shadow-inner"
                  value={details}
                  onChange={(e) => setDetails(e.target.value)}
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button 
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-8 py-4 text-sm font-black text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-widest"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  disabled={!selectedReason || isSubmitting}
                  className="flex-[2] px-8 py-4 bg-red-600 text-white text-sm font-black rounded-3xl hover:bg-red-700 transition-all shadow-xl shadow-red-100 disabled:opacity-50 disabled:shadow-none uppercase tracking-widest"
                >
                  {isSubmitting ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Submitting...
                    </span>
                  ) : 'Submit Report'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default ReportModal;
