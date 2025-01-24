import { Text } from "@react-three/drei";
import React, { useRef } from "react";
import { Mesh } from "three";

import { Languages, Language } from "./utils";

export const SCALE = 10;

interface DotProps {
  word: string;
  x: number;
  y: number;
  z: number;
  selected: boolean;
  select: () => void;
  searchPending?: boolean;
  language?: string | null;
}

const Dot: React.FC<DotProps> = ({
  word,
  x,
  y,
  z,
  selected,
  select,
  searchPending = false,
  language,
}) => {
  const meshRef = useRef<Mesh>(null);
  const dotColor = language
    ? Languages.find((l: Language) => l.name === language)?.color
    : "white";

  return (
    <mesh
      ref={meshRef}
      position={[x * SCALE, y * SCALE, z * SCALE]}
      onClick={select}
    >
      <sphereGeometry args={[0.15 * (selected ? 1.2 : 1), 32, 32]} />
      <meshStandardMaterial
        color={dotColor}
        emissive={dotColor}
        transparent
        opacity={searchPending ? 0.25 : selected ? 1 : 0.5}
      />
      <Text
        position={[0, 0.5, 0]}
        fontSize={0.3}
        color={dotColor}
        transparent={!selected}
      >
        {word}
      </Text>
    </mesh>
  );
};

export default Dot;
