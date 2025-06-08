// ILP – Individual Launch Point UI-Komponente mit realistischer Rückwärtssimulation

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectItem, SelectContent } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import MapWithCircle from "@/components/map/MapWithCircle";
import * as utm from "utm";

const exampleWindProfile = [
  { height: 0, wind: [1.0, 0.0] },
  { height: 500, wind: [0.5, 0.5] },
  { height: 1000, wind: [0.0, 1.0] },
  { height: 1500, wind: [-0.5, 0.5] },
  { height: 2000, wind: [-1.0, 0.0] }
];

export default function ILPPage() {
  const [utmZone, setUtmZone] = useState("33T");
  const [format, setFormat] = useState("4/4");
  const [utmEast, setUtmEast] = useState(654200);
  const [utmNorth, setUtmNorth] = useState(5231170);
  const [rangeKm, setRangeKm] = useState([2, 10]);
  const [heightLimits, setHeightLimits] = useState([0, 3000]);
  const [rateLimit, setRateLimit] = useState(2);
  const [latlon, setLatlon] = useState({ lat: 0, lon: 0 });
  const [ilpResults, setIlpResults] = useState(null);

  function handleUTMChange() {
    try {
      const zoneNumber = parseInt(utmZone.slice(0, -1));
      const zoneLetter = utmZone.slice(-1);
      const { latitude, longitude } = utm.toLatLon(utmEast, utmNorth, zoneNumber, zoneLetter);
      setLatlon({ lat: latitude, lon: longitude });
    } catch (err) {
      setLatlon({ lat: 0, lon: 0 });
    }
  }

  function simulateILP() {
    handleUTMChange();
    const zoneNumber = parseInt(utmZone.slice(0, -1));
    const zoneLetter = utmZone.slice(-1);

    const activeWinds = exampleWindProfile.filter(w => w.height >= heightLimits[0] && w.height <= heightLimits[1]);

    const candidatePoints = activeWinds.map(w => {
      const h = w.height; // ft
      const h_m = h * 0.3048; // in m
      const t = (2 * h_m) / rateLimit; // Zeit für Auf- und Abstieg in Sekunden
      const dx = -w.wind[0] * t; // Rückwärtssimulation (negativer Windvektor)
      const dy = -w.wind[1] * t;
      return {
        easting: utmEast + dx,
        northing: utmNorth + dy
      };
    });

    const avg = candidatePoints.reduce((acc, p) => ({
      easting: acc.easting + p.easting,
      northing: acc.northing + p.northing
    }), { easting: 0, northing: 0 });

    const center = {
      easting: avg.easting / candidatePoints.length,
      northing: avg.northing / candidatePoints.length
    };

    const { latitude, longitude } = utm.toLatLon(center.easting, center.northing, zoneNumber, zoneLetter);

    setIlpResults({
      center: { lat: latitude, lon: longitude },
      radiusKm: rangeKm[1],
      easting: center.easting,
      northing: center.northing
    });
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">ILP – Individual Launch Point</h1>

      <Card>
        <CardContent className="space-y-2">
          <Label>UTM-Zone</Label>
          <Select value={utmZone} onValueChange={v => setUtmZone(v)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="32T">32T</SelectItem>
              <SelectItem value="33T">33T</SelectItem>
              <SelectItem value="34T">34T</SelectItem>
            </SelectContent>
          </Select>

          <Label>Koordinatenformat</Label>
          <Select value={format} onValueChange={v => setFormat(v)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="4/4">4/4</SelectItem>
              <SelectItem value="5/4">5/4</SelectItem>
            </SelectContent>
          </Select>

          <Label>UTM-Ostwert</Label>
          <Input type="number" value={utmEast} onChange={e => setUtmEast(Number(e.target.value))} onBlur={handleUTMChange} />

          <Label>UTM-Nordwert</Label>
          <Input type="number" value={utmNorth} onChange={e => setUtmNorth(Number(e.target.value))} onBlur={handleUTMChange} />

          <div>
            <p className="text-sm text-gray-500">WGS 84 Koordinaten (nur intern): {latlon.lat.toFixed(6)} N, {latlon.lon.toFixed(6)} E</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4">
          <Label>Erlaubte Startdistanz vom Ziel (km)</Label>
          <Slider min={1} max={50} step={1} value={rangeKm} onValueChange={setRangeKm} range />
          <p>{rangeKm[0]} km – {rangeKm[1]} km</p>

          <Label>Erlaubte Höhen (ft MSL)</Label>
          <Slider min={0} max={10000} step={100} value={heightLimits} onValueChange={setHeightLimits} range />
          <p>{heightLimits[0]} ft – {heightLimits[1]} ft</p>

          <Label>Maximale Steig-/Sinkrate (m/s)</Label>
          <Slider min={0} max={8} step={0.5} value={[rateLimit]} onValueChange={v => setRateLimit(v[0])} />
          <p>{rateLimit} m/s</p>

          <Button onClick={simulateILP}>ILP-Bereich berechnen</Button>
        </CardContent>
      </Card>

      {ilpResults && (
        <MapWithCircle lat={ilpResults.center.lat} lon={ilpResults.center.lon} radiusKm={rangeKm[1]} />
      )}
    </div>
  );
}
