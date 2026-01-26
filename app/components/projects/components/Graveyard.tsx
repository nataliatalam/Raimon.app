'use client';

import React, { useMemo, useState } from 'react';
import { X, Sparkles, PenTool } from 'lucide-react';
import type { GraveyardProject, Flower } from '../types';
import styles from './Graveyard.module.css';

interface GraveyardProps {
  projects: GraveyardProject[];
  flowerPoints: number;
  onKillProject: (id: number) => void;
  onBuyFlower: (projectId: number, flower: Flower) => void;
  onResurrect: (projectId: number) => void;
  onWriteEpitaph: (projectId: number, message: string) => void;
}

const FLOWERS: Flower[] = [
  { id: 'daisy', name: 'Daisy', emoji: '🌼', cost: 1, daysAdded: 7 },
  { id: 'rose', name: 'Rose', emoji: '🌹', cost: 3, daysAdded: 14 },
  { id: 'sunflower', name: 'Sunflower', emoji: '🌻', cost: 5, daysAdded: 30 },
  { id: 'lotus', name: 'Lotus', emoji: '🪷', cost: 10, daysAdded: 90 },
];

export default function Graveyard({
  projects,
  flowerPoints,
  onKillProject,
  onBuyFlower,
  onResurrect,
  onWriteEpitaph,
}: GraveyardProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedGrave, setSelectedGrave] = useState<number | null>(null);
  const [epitaphInput, setEpitaphInput] = useState('');

  const selected = useMemo(
    () => projects.find((p) => p.id === selectedGrave) || null,
    [projects, selectedGrave]
  );

  function onDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    const projectId = e.dataTransfer.getData('projectId');
    if (projectId) onKillProject(parseInt(projectId, 10));
  }

  const RESURRECTION_COST = 25;
  const EPITAPH_COST = 5;

  return (
    <section className={styles.wrap}>
      <div className={styles.head}>
        <div>
          <div className={styles.kicker}>ARCHIVE</div>
          <h2 className={styles.title}>The Graveyard</h2>
          <p className={styles.sub}>
            Drag abandoned projects to the rock. Spend flower points to extend memory or resurrect it.
          </p>
        </div>

        <div className={styles.pointsPill}>
          <span className={styles.pointsLabel}>Points</span>
          <span className={styles.pointsValue}>{flowerPoints} 🌸</span>
        </div>
      </div>

      <div className={styles.grid}>
        {/* Rock */}
        <div
          className={[styles.rock, isDragOver ? styles.rockActive : ''].join(' ')}
          onDragOver={onDragOver}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={onDrop}
        >
          <div className={styles.rockEmoji} aria-hidden="true">
            🪨
          </div>
          <div className={styles.rockTitle}>Rock of Acceptance</div>
          <div className={styles.rockHint}>Drop an active project here to end it.</div>
        </div>

        {/* Tombstones */}
        <div className={styles.stones}>
          {projects.length === 0 ? (
            <div className={styles.empty}>No dreams have been abandoned… yet.</div>
          ) : (
            projects.map((p) => {
              const daysLeft = Math.max(
                0,
                Math.ceil((p.expiryDate - Date.now()) / (1000 * 60 * 60 * 24))
              );

              return (
                <button
                  key={p.id}
                  className={styles.stone}
                  onClick={() => {
                    setSelectedGrave(p.id);
                    setEpitaphInput(p.epitaph || '');
                  }}
                  type="button"
                >
                  <div className={styles.stoneInner}>
                    <div className={styles.stoneTop}>
                      <div className={styles.hereLies}>Here lies</div>
                      <div className={styles.name}>{p.name}</div>
                      <div className={styles.meta}>{p.type.toUpperCase()}</div>
                      {p.epitaph && (
                        <div className={styles.epitaph}>&ldquo;{p.epitaph}&rdquo;</div>
                      )}
                    </div>

                    <div className={styles.fadeRow}>
                      <span>Fades in</span>
                      <strong>{daysLeft}d</strong>
                    </div>
                  </div>

                  <div className={styles.flowers}>
                    {p.flowers.map((f, i) => (
                      <span key={i} title={f.name}>
                        {f.emoji}
                      </span>
                    ))}
                  </div>

                  <div className={styles.stoneHover}>
                    <span className={styles.connect}>
                      <Sparkles size={14} />
                      Connect Spirit
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Modal */}
      {selectedGrave && selected && (
        <div className={styles.modalOverlay} role="dialog" aria-modal="true">
          <div className={styles.modal}>
            <div className={styles.modalHead}>
              <div>
                <div className={styles.modalKicker}>SPIRIT CONNECTION</div>
                <div className={styles.modalTitle}>{selected.name}</div>
                <div className={styles.modalSub}>Choose how to interact with this memory.</div>
              </div>

              <button className={styles.closeBtn} onClick={() => setSelectedGrave(null)} type="button">
                <X size={18} />
              </button>
            </div>

            {/* Offerings */}
            <div className={styles.block}>
              <div className={styles.blockTitle}>Offerings</div>
              <div className={styles.offeringGrid}>
                {FLOWERS.map((f) => {
                  const can = flowerPoints >= f.cost;
                  return (
                    <button
                      key={f.id}
                      className={[styles.offerBtn, !can ? styles.disabled : ''].join(' ')}
                      disabled={!can}
                      onClick={() => {
                        onBuyFlower(selectedGrave, f);
                        setSelectedGrave(null);
                      }}
                      type="button"
                    >
                      <div className={styles.offerEmoji}>{f.emoji}</div>
                      <div className={styles.offerMeta}>
                        <div className={styles.offerCost}>{f.cost} pts</div>
                        <div className={styles.offerDays}>+{f.daysAdded}d</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Epitaph */}
            <div className={styles.block}>
              <div className={styles.blockTitle}>Carve epitaph ({EPITAPH_COST} pts)</div>
              <div className={styles.epitaphRow}>
                <input
                  className={styles.input}
                  value={epitaphInput}
                  onChange={(e) => setEpitaphInput(e.target.value)}
                  placeholder="e.g. Not now — maybe later."
                  maxLength={40}
                />
                <button
                  className={styles.writeBtn}
                  disabled={flowerPoints < EPITAPH_COST || !epitaphInput.trim()}
                  onClick={() => {
                    onWriteEpitaph(selectedGrave, epitaphInput);
                    setSelectedGrave(null);
                  }}
                  title="Save epitaph"
                  type="button"
                >
                  <PenTool size={16} />
                </button>
              </div>
            </div>

            {/* Resurrection */}
            <div className={styles.ritual}>
              <div className={styles.ritualLeft}>
                <div className={styles.ritualTitle}>
                  <Sparkles size={16} />
                  Resurrection Ritual
                </div>
                <div className={styles.ritualSub}>Bring it back as a paused flow.</div>
              </div>

              <button
                className={styles.reviveBtn}
                disabled={flowerPoints < RESURRECTION_COST}
                onClick={() => {
                  onResurrect(selectedGrave);
                  setSelectedGrave(null);
                }}
                type="button"
              >
                Revive ({RESURRECTION_COST} pts)
              </button>
            </div>

            <div className={styles.balance}>
              Balance: <strong>{flowerPoints}</strong> flower points
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
