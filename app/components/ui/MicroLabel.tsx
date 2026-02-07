'use client';

import React from 'react';

interface MicroLabelProps {
  text: string;
  color?: string;
}

const MicroLabel: React.FC<MicroLabelProps> = ({ text, color = 'text-zinc-400' }) => {
  return (
    <span className={`text-[9px] font-black uppercase tracking-[0.2em] ${color}`}>
      {text}
    </span>
  );
};

export default MicroLabel;
