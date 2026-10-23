"use client";

import { geoGraticule10, geoNaturalEarth1, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import { Minus, Plus, RotateCcw, MapPinOff } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";

type CountryProperties = { name: string };
type Atlas = Topology<{ countries: GeometryCollection<CountryProperties> }>;
type CountryCollection = FeatureCollection<Geometry, CountryProperties>;

export default function WorldRiskMap({ reason }: { reason: string }) {
  const [countries, setCountries] = useState<CountryCollection | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [selected, setSelected] = useState("");
  const [hovered, setHovered] = useState("");
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    fetch("/maps/countries-110m.json", { signal: controller.signal, cache: "force-cache" })
      .then(async response => {
        if (!response.ok) throw new Error("Basemap unavailable");
        const topology = await response.json() as Atlas;
        return feature(topology, topology.objects.countries);
      })
      .then(value => setCountries(value))
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [attempt]);
  const projection = useMemo(() => geoNaturalEarth1().fitExtent(
    [[14, 14], [786, 414]], { type: "Sphere" },
  ), []);
  const path = useMemo(() => geoPath(projection), [projection]);
  const options = useMemo(() => [...(countries?.features ?? [])].sort(
    (a, b) => a.properties.name.localeCompare(b.properties.name, "en"),
  ), [countries]);
  const country = options.find(item => item.properties.name === selected);
  const transform = useMemo(() => {
    if (country) {
      const [[x0, y0], [x1, y1]] = path.bounds(country);
      const scale = Math.min(5, .72 / Math.max((x1 - x0) / 800, (y1 - y0) / 430));
      return `translate(400 215) scale(${scale * zoom}) translate(${-(x0 + x1) / 2 + pan.x} ${-(y0 + y1) / 2 + pan.y})`;
    }
    return `translate(400 215) scale(${zoom}) translate(${-400 + pan.x} ${-215 + pan.y})`;
  }, [country, path, zoom, pan]);
  function reset() { setSelected(""); setZoom(1); setPan({ x: 0, y: 0 }); }
  return <div className="world-map">
    <div className="world-map-toolbar"><label htmlFor="country-filter">Region</label><select id="country-filter" aria-label="Map country" value={selected} onChange={event => { setSelected(event.target.value); setZoom(1); setPan({ x: 0, y: 0 }); }}>
      <option value="">All countries</option>{options.map(item => <option key={item.properties.name + item.properties.name} value={item.properties.name}>{item.properties.name}</option>)}
    </select><span>Basemap · Risk data unavailable</span></div>
    <div className="world-map-canvas">
      {error ? <div className="empty-state" role="alert">The world basemap could not be loaded.<button className="secondary" onClick={() => setAttempt(value => value + 1)}>Retry map</button></div> : !countries ? <div className="empty-state" role="status">Loading world basemap…</div> :
        <svg viewBox="0 0 800 430" role="img" aria-label="World country map. Country boundaries are displayed; risk location data is unavailable." tabIndex={0} onKeyDown={event => {
          const moves: Record<string, [number, number]> = { ArrowLeft: [20, 0], ArrowRight: [-20, 0], ArrowUp: [0, 20], ArrowDown: [0, -20] };
          if (moves[event.key]) {
            event.preventDefault();
            const [dx, dy] = moves[event.key]; setPan(p => ({ x: Math.max(-400, Math.min(400, p.x + dx)), y: Math.max(-215, Math.min(215, p.y + dy)) }));
          } else if (event.key === "+" || event.key === "=") setZoom(z => Math.min(4, z + .5));
          else if (event.key === "-") setZoom(z => Math.max(1, z - .5));
          else if (event.key === "Escape") reset();
        }}>
          <defs><pattern id="world-map-dots" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".8" fill="#41a0ae" opacity=".4"/></pattern></defs>
          <g transform={transform}>
            <path d={path({ type: "Sphere" }) ?? ""} className="world-map-ocean"/>
            <path d={path(geoGraticule10()) ?? ""} className="world-map-graticule"/>
            {countries.features.map(item => <path key={item.properties.name + item.properties.name} d={path(item) ?? ""} className={`world-map-country ${selected === item.properties.name ? "selected" : ""}`} fill="url(#world-map-dots)" onMouseEnter={() => setHovered(item.properties.name)} onMouseLeave={() => setHovered("")} onClick={() => { setSelected(item.properties.name); setZoom(1); setPan({ x: 0, y: 0 }); }}>
              <title>{`${item.properties.name} — verified risk location data unavailable`}</title>
            </path>)}
          </g>
        </svg>}
      {(hovered || country) && <div className="world-map-tooltip" role="status"><strong>{hovered || country?.properties.name}</strong><span>Verified risk locations unavailable</span></div>}
      <div className="world-map-controls"><button aria-label="Zoom in map" disabled={zoom >= 4} onClick={() => setZoom(z => Math.min(4, z + .5))}><Plus size={14}/></button><button aria-label="Zoom out map" disabled={zoom <= 1} onClick={() => setZoom(z => Math.max(1, z - .5))}><Minus size={14}/></button><button aria-label="Reset world map" onClick={reset}><RotateCcw size={13}/></button></div>
    </div>
    <div className="map-availability"><MapPinOff size={15}/><p><strong>Geographic risk layer unavailable</strong><span>{reason}</span></p></div>
    <div className="world-map-credit"><a href="https://github.com/topojson/world-atlas" target="_blank" rel="noreferrer">Natural Earth / World Atlas</a><span>Arrow keys pan · + / − zoom · Esc reset</span></div>
  </div>;
}
