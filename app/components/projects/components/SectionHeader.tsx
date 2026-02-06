'use client';

type SectionVariant = 'active' | 'paused' | 'beyond';

interface SectionHeaderProps {
  title: string;
  count: number;
  variant: SectionVariant;
}

export default function SectionHeader({ title, count }: SectionHeaderProps) {
  return (
    <div className="flex items-center gap-4 mb-6">
      {/* Title */}
      <h2 className="text-3xl font-semibold text-slate-800 tracking-tight">{title}</h2>

      {/* Gray Line */}
      <div className="h-px flex-1 bg-slate-200"></div>

      {/* Count Badge */}
      <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">{count} Projects</span>
    </div>
  );
}
