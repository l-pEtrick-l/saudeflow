import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import type { Unit } from "../lib/types";

const COLORS: Record<string, string> = {
  ubs: "#10b981",
  upa: "#1b6ef5",
  hospital: "#8b5cf6",
  emergency: "#ef4444",
};

export function UnitMap({
  units,
  height = 420,
  onSelect,
}: {
  units: Unit[];
  height?: number;
  onSelect?: (unit: Unit) => void;
}) {
  const located = units.filter((u) => u.latitude != null && u.longitude != null);
  const center: [number, number] = located.length
    ? [located[0].latitude as number, located[0].longitude as number]
    : [-23.5505, -46.6333];

  return (
    <div style={{ height }} className="overflow-hidden rounded-2xl border border-slate-200">
      <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {located.map((unit) => (
          <Marker
            key={unit.id}
            position={[unit.latitude as number, unit.longitude as number]}
            eventHandlers={{ click: () => onSelect?.(unit) }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold" style={{ color: COLORS[unit.type] }}>
                  {unit.name}
                </p>
                <p className="text-slate-600">
                  {unit.type.toUpperCase()} · {unit.neighborhood || "—"}, {unit.city}
                </p>
                {unit.distance_km != null && <p>Distância aproximada: {unit.distance_km} km</p>}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
