import React from 'react';

const Logo = () => {
  return (
    <div className="pointer-events-none">
      <svg width="400" height="100" xmlns="http://www.w3.org/2000/svg">
        <text x="0" y="75" style={{ fontFamily: 'Arial, sans-serif', fontSize: '50px', fontWeight: 'bold', fill: 'white' }}>DA</text>
        <text x="80" y="75" style={{ fontFamily: 'Arial, sans-serif', fontSize: '80px', fontWeight: 'bold', fill: 'white' }}>VINCHI</text>
      </svg>
    </div>
  );
};

export default Logo;
