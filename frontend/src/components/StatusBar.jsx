import { useState, useEffect } from 'react';

export default function StatusBar() {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false }));
    };
    update();
    const iv = setInterval(update, 10000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="status-bar">
      <span className="status-bar__time">{time}</span>
      <div className="status-bar__icons">
        <span className="material-symbols-outlined icon" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>signal_cellular_alt</span>
        <span className="material-symbols-outlined icon" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>wifi</span>
        <span className="material-symbols-outlined icon" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>battery_5_bar</span>
      </div>
    </div>
  );
}
