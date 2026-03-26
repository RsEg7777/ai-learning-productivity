'use client';

import React, { useEffect, useRef, useState } from "react";

const CustomCursor: React.FC = () => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const [isHovering, setIsHovering] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const style = document.createElement("style");
    style.id = "custom-cursor-styles";
    style.innerHTML = `
      * {
        cursor: none !important;
      }
      input, textarea, [contenteditable="true"] {
        caret-color: #6366f1 !important;
      }
      ::selection {
        background: rgba(99, 102, 241, 0.3);
        color: white;
      }
    `;
    document.head.appendChild(style);
    document.body.style.cursor = "none";

    const showCursor = () => setVisible(true);
    document.addEventListener("mousemove", showCursor, { once: true });

    return () => {
      const existingStyle = document.getElementById("custom-cursor-styles");
      if (existingStyle) existingStyle.remove();
      document.body.style.cursor = "auto";
      document.removeEventListener("mousemove", showCursor);
    };
  }, []);

  useEffect(() => {
    const moveCursor = (e: MouseEvent) => {
      if (cursorRef.current) {
        // Center the cursor on the mouse point
        cursorRef.current.style.transform = `translate3d(calc(${e.clientX}px - 50%), calc(${e.clientY}px - 50%), 0)`;
      }
    };

    const interactiveSelectors = [
      "a", "button", "[role=button]", "input", "select", "textarea",
      "label", "[tabindex]:not([tabindex='-1'])", ".btn", ".clickable"
    ];
    const selector = interactiveSelectors.join(", ");

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as Element;
      if (target.matches?.(selector)) setIsHovering(true);
    };

    const handleMouseOut = (e: MouseEvent) => {
      const target = e.target as Element;
      const related = e.relatedTarget as Element | null;
      if (target.matches?.(selector) && !related?.matches?.(selector)) {
        setIsHovering(false);
      }
    };

    document.addEventListener("mousemove", moveCursor);
    document.addEventListener("mouseover", handleMouseOver);
    document.addEventListener("mouseout", handleMouseOut);

    return () => {
      document.removeEventListener("mousemove", moveCursor);
      document.removeEventListener("mouseover", handleMouseOver);
      document.removeEventListener("mouseout", handleMouseOut);
    };
  }, []);

  if (!visible) return null;

  return (
    <div
      ref={cursorRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: isHovering ? "40px" : "32px", // Slightly smaller on hover
        height: isHovering ? "40px" : "32px",
        borderRadius: "50%",
        backgroundColor: isHovering
          ? "rgba(99, 102, 241, 0.1)"  // More transparent
          : "rgba(255, 255, 255, 0.05)",
        border: isHovering
          ? "2px solid rgba(99, 102, 241, 0.6)"
          : "1px solid rgba(255, 255, 255, 0.2)",
        boxShadow: isHovering
          ? "0 0 20px rgba(99, 102, 241, 0.4)"
          : "0 0 10px rgba(255, 255, 255, 0.1)",
        // backdropFilter removed – no more blurring of text
        pointerEvents: "none",
        zIndex: 99999,
        transform: "translate3d(0,0,0)",
        transition: "width 0.2s, height 0.2s, background-color 0.2s, border 0.2s, box-shadow 0.2s",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      aria-hidden="true"
    >
      {/* Inner dot – always at the exact pointer */}
      <div
        style={{
          width: "4px",
          height: "4px",
          borderRadius: "50%",
          backgroundColor: isHovering ? "#6366f1" : "rgba(255,255,255,0.8)",
          transition: "background-color 0.2s",
        }}
      />
    </div>
  );
};

export default CustomCursor;