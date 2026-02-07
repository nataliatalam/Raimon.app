'use client';

import React, { useState } from 'react';

interface GuideDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const GuideDrawer: React.FC<GuideDrawerProps> = ({ isOpen, onClose }) => {
  const [googleSync, setGoogleSync] = useState(false);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/30 backdrop-blur-md z-40 transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div className={`fixed top-4 right-4 bottom-4 w-full max-w-md bg-black text-white rounded-[3.5rem] shadow-2xl z-50 transform transition-transform duration-500 ease-out border border-white/10 ${isOpen ? 'translate-x-0' : 'translate-x-[110%]'}`}>
        <div className="h-full flex flex-col p-12 overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-12">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center font-black text-lg text-black">R</div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight">The Raimon <span className="text-orange-500">Method</span></h2>
                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Mastering your focus</p>
              </div>
            </div>
            <button onClick={onClose} className="p-3 hover:bg-white/10 rounded-full transition-colors">
              <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          <div className="space-y-12">
            {/* Section 1: Interaction Guide */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[11px] font-black">01</div>
                <h3 className="text-xs font-black uppercase tracking-widest text-orange-400">Interaction</h3>
              </div>

              <div className="bg-white/5 p-8 rounded-[2.5rem] border border-white/5 group hover:bg-white/10 transition-all">
                <h4 className="text-lg font-bold text-white mb-3">The Perfect Slot</h4>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Click any empty space to <span className="text-white font-bold">instantly add events, deadlines, or time blocks</span>. Change details by simply tapping and updating.
                </p>
              </div>
            </div>

            {/* Section 2: Sync Settings */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[11px] font-black">02</div>
                <h3 className="text-xs font-black uppercase tracking-widest text-orange-400">Connections</h3>
              </div>

              <div className="bg-white/5 p-8 rounded-[2.5rem] border border-white/5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
                      <svg className="w-6 h-6" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">Google Calendar</h4>
                      <p className="text-[10px] text-gray-500 font-bold uppercase tracking-tight">Coming Soon</p>
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <button
                    onClick={() => setGoogleSync(!googleSync)}
                    className={`w-12 h-6 rounded-full transition-colors relative flex items-center px-1 ${googleSync ? 'bg-orange-500' : 'bg-gray-700'}`}
                  >
                    <div className={`w-4 h-4 bg-white rounded-full shadow-sm transform transition-transform ${googleSync ? 'translate-x-6' : 'translate-x-0'}`} />
                  </button>
                </div>
                <p className="text-[11px] text-gray-400 leading-snug">
                  When enabled, Raimon will automatically sync your calendar with Google. Import your external invites and export your scheduled events. No double-booking, ever.
                </p>
                {googleSync && (
                  <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/20 rounded-xl">
                    <p className="text-[10px] text-orange-400 font-bold">Google Calendar integration is coming soon. We&apos;ll notify you when it&apos;s ready!</p>
                  </div>
                )}
              </div>
            </div>

            {/* Section 3: Visual Logic */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[11px] font-black">03</div>
                <h3 className="text-xs font-black uppercase tracking-widest text-orange-400">Visuals</h3>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-4 rounded-[1.5rem] border border-white/10 bg-black text-center flex flex-col items-center">
                  <div className="w-4 h-4 bg-white border border-gray-600 rounded-full mb-2"></div>
                  <span className="text-[9px] font-black uppercase tracking-widest text-gray-400">Work</span>
                </div>
                <div className="p-4 rounded-[1.5rem] border border-orange-500/30 bg-orange-500/5 text-center flex flex-col items-center">
                  <div className="w-4 h-4 bg-orange-500 rounded-full mb-2 shadow-[0_0_10px_rgba(249,115,22,0.4)]"></div>
                  <span className="text-[9px] font-black uppercase tracking-widest text-orange-500">Personal</span>
                </div>
                <div className="p-4 rounded-[1.5rem] border border-blue-500/30 bg-blue-500/5 text-center flex flex-col items-center">
                  <div className="w-4 h-4 bg-blue-400 rounded-full mb-2 shadow-[0_0_10px_rgba(96,165,250,0.4)]"></div>
                  <span className="text-[9px] font-black uppercase tracking-widest text-blue-400">Other</span>
                </div>
              </div>
            </div>

            {/* Section 4: Tips */}
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[11px] font-black">04</div>
                <h3 className="text-xs font-black uppercase tracking-widest text-orange-400">Pro Tips</h3>
              </div>

              <div className="space-y-3">
                <div className="bg-white/5 p-5 rounded-2xl border border-white/5">
                  <p className="text-[11px] text-gray-400 leading-relaxed">
                    <span className="text-white font-bold">Project Deadlines:</span> Your project deadlines will automatically appear on your calendar.
                  </p>
                </div>
                <div className="bg-white/5 p-5 rounded-2xl border border-white/5">
                  <p className="text-[11px] text-gray-400 leading-relaxed">
                    <span className="text-white font-bold">Quick Views:</span> Switch between Day, Week, and Month views using the toggle at the top.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Footer Quote */}
          <div className="mt-auto pt-12 text-center">
            <p className="text-sm text-gray-500 italic font-medium leading-relaxed">
              &quot;You don&apos;t need more time. You need more clarity.&quot;
            </p>
            <div className="mt-8 h-1 w-16 bg-orange-500 mx-auto rounded-full opacity-40"></div>
          </div>
        </div>
      </div>
    </>
  );
};

export default GuideDrawer;
