import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="brand-header" role="banner">
      <div className="brand-logo-container">
        {/* YETI wordmark SVG representation */}
        <svg
          className="yeti-wordmark"
          viewBox="0 0 160 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-label="YETI logo"
        >
          <path
            d="M0 4.8h11.6l8.8 14.5 8.7-14.5h11.5L26.4 26.8v16.4H14.3V26.8L0 4.8zM44.2 4.8h33.2v9.4H56.3v4.6h18.2v9.2H56.3v5.8h21.9v9.4H44.2V4.8zM92.2 14.2H79.6V4.8h37.4v9.4h-12.7v29h-12.1v-29zM122.8 4.8h12.1v38.4h-12.1V4.8z"
            fill="#06263F"
          />
          {/* Registered trademark symbol */}
          <circle cx="143" cy="7.5" r="4.5" stroke="#06263F" strokeWidth="1" fill="none" />
          <text x="143" y="9.8" fontSize="6" fontWeight="bold" fill="#06263F" textAnchor="middle">R</text>
        </svg>
      </div>
      <h1 className="brand-title">AD GENERATOR</h1>
    </header>
  );
};
