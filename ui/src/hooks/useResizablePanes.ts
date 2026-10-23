import { useState, useCallback, useEffect, useRef } from 'react';

interface ResizeState {
  leftWidth: number;
  rightWidth: number | null;
}

const MIN_LEFT = 200;
const MAX_LEFT = 480;
const MIN_RIGHT = 280;
const MAX_RIGHT = 520;

export function useResizablePanes(defaultLeft = 240, defaultRight = 360) {
  const [leftWidth, setLeftWidth] = useState(defaultLeft);
  const [rightWidth, setRightWidth] = useState<number | null>(defaultRight);
  const [activeHandle, setActiveHandle] = useState<'left' | 'right' | null>(null);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const onMouseMove = useCallback((e: MouseEvent) => {
    const delta = e.clientX - startXRef.current;
    if (activeHandle === 'left') {
      const newWidth = Math.max(MIN_LEFT, Math.min(MAX_LEFT, startWidthRef.current + delta));
      setLeftWidth(newWidth);
    } else if (activeHandle === 'right') {
      const newWidth = Math.max(MIN_RIGHT, Math.min(MAX_RIGHT, startWidthRef.current - delta));
      setRightWidth(newWidth);
    }
  }, [activeHandle]);

  const onMouseUp = useCallback(() => {
    setActiveHandle(null);
  }, []);

  useEffect(() => {
    if (activeHandle) {
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      return () => {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [activeHandle, onMouseMove, onMouseUp]);

  const startLeftResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    startXRef.current = e.clientX;
    startWidthRef.current = leftWidth;
    setActiveHandle('left');
  }, [leftWidth]);

  const startRightResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    startXRef.current = e.clientX;
    startWidthRef.current = rightWidth ?? defaultRight;
    setActiveHandle('right');
  }, [rightWidth, defaultRight]);

  return {
    leftWidth,
    rightWidth,
    activeHandle,
    startLeftResize,
    startRightResize,
    setRightWidth,
  };
}
