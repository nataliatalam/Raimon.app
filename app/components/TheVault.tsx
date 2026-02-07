'use client';

import React from 'react';
import { Link2, FileText, StickyNote, ArrowUpRight } from 'lucide-react';
import type { FocusResource } from './FocusChamber';

interface TheVaultProps {
  resources: FocusResource[];
}

const TheVault: React.FC<TheVaultProps> = ({ resources }) => {
  const getResourceStyles = (kind: FocusResource['kind']) => {
    switch (kind) {
      case 'link':
        return { icon: <Link2 size={12} />, accent: 'text-blue-400', bg: 'bg-blue-400/10' };
      case 'doc':
        return { icon: <FileText size={12} />, accent: 'text-indigo-400', bg: 'bg-indigo-400/10' };
      case 'sheet':
        return { icon: <StickyNote size={12} />, accent: 'text-[#FF6B00]', bg: 'bg-[#FF6B00]/10' };
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0D1117] relative overflow-hidden">
      {/* Decorative Blur */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-[#FF6B00]/10 rounded-full blur-[80px] pointer-events-none" />

      {/* Header */}
      <div className="px-6 pt-6 pb-3 shrink-0">
        <h2 className="text-3xl font-black text-[#FF6B00] tracking-tighter leading-none mb-1">
          Resources
        </h2>
        <p className="text-white/60 text-[10px] font-medium tracking-tight">
          Everything you need for this session.
        </p>
      </div>

      {/* Resource List */}
      <div className="flex-1 px-5 py-3 flex flex-col gap-2 overflow-y-auto">
        {resources.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-white/30 text-sm font-medium">No resources attached</p>
          </div>
        ) : (
          resources.map((res) => {
            const styles = getResourceStyles(res.kind);
            return (
              <button
                key={res.id}
                type="button"
                onClick={res.onClick}
                className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 hover:shadow-2xl hover:shadow-black/20 transition-all duration-300 group cursor-pointer text-left"
              >
                <div className="flex items-center gap-3">
                  <div className={`h-8 w-8 rounded-lg ${styles.bg} ${styles.accent} flex items-center justify-center transition-all group-hover:scale-110`}>
                    {styles.icon}
                  </div>
                  <div>
                    <p className="text-[11px] font-black text-white uppercase tracking-wider">{res.name}</p>
                    <p className={`text-[8px] font-black uppercase tracking-[0.2em] mt-0.5 ${styles.accent}`}>
                      {res.action ?? 'Open'}
                    </p>
                  </div>
                </div>
                <ArrowUpRight size={14} className="text-white/20 group-hover:text-white transition-all" />
              </button>
            );
          })
        )}

        {/* End indicator */}
        {resources.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-center gap-2">
            <div className="w-1 h-1 rounded-full bg-white/10" />
            <div className="w-1 h-1 rounded-full bg-white/10" />
            <div className="w-1 h-1 rounded-full bg-white/10" />
          </div>
        )}
      </div>
    </div>
  );
};

export default TheVault;
