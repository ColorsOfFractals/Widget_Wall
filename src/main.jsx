const widgetCatalog = [
  { id: "scratchpad", name: "SCRATCHPAD", icon: "✎",
    description: "Floating notes with copy and clear." },
  { id: "counter", name: "COUNTER", icon: "#",
    description: "A tiny increment/decrement counter." },
  { id: "clock", name: "CLOCK", icon: "◷",
    description: "Live desktop clock with seconds." }
];

const libraryCatalog = [
  {id:'scratchpad',name:'Scratchpad',category:'Productivity',description:'Floating notes with Copy and Clear.',ready:true},
  {id:'counter',name:'Counter',category:'Productivity',description:'Increment, decrement, and reset.',ready:true},
  {id:'clock',name:'Digital Clock',category:'Time & Planning',description:'Live clock with seconds.',ready:true},
  {id:'weather',name:'Pocket Weather',category:'Information & Web',description:'Animated transparent weather sprite. Drag anywhere; right-click for live city weather.',ready:true},
  {id:'analog-clock',name:'Analog Clock',category:'Time & Planning',description:'Classic clock face.'},
  {id:'photo-frame',name:'Photo Frame',category:'Desktop & Media',description:'Rotating personal photos.'},
  {id:'stocks',name:'Stock Ticker',category:'Information & Web',description:'Market watchlist.'},
  {id:'calendar',name:'Calendar',category:'Time & Planning',description:'Dates and appointments.'},
  {id:'email',name:'Email Checker',category:'Information & Web',description:'Unread message indicator.'},
  {id:'system',name:'CPU / RAM Monitor',category:'System & Hardware',description:'Live system resource usage.'},
  {id:'battery',name:'Battery Monitor',category:'System & Hardware',description:'Battery and charging state.'},
  {id:'rss',name:'RSS News Reader',category:'Information & Web',description:'Headline feeds.'},
  {id:'calculator',name:'Calculator',category:'Productivity',description:'Quick arithmetic.'},
  {id:'todo',name:'To-Do List',category:'Productivity',description:'Small task checklist.'},
  {id:'currency',name:'Currency Converter',category:'Information & Web',description:'Foreign exchange calculations.'},
  {id:'search',name:'Web Search',category:'Productivity',description:'Quick search launcher.'},
  {id:'dictionary',name:'Dictionary',category:'Information & Web',description:'Word definitions.'},
  {id:'music',name:'Music Player',category:'Desktop & Media',description:'Playback controls.'},
  {id:'network',name:'Network Monitor',category:'System & Hardware',description:'Network interface statistics.'},
  {id:'countdown',name:'Countdown Timer',category:'Time & Planning',description:'Countdown to an event.'},
  {id:'recycle',name:'Recycle Bin',category:'Desktop & Media',description:'Trash status and actions.'}
];
const libraryCategories = ['All Widgets','System & Hardware','Time & Planning','Productivity','Information & Web','Desktop & Media'];
let nativeBridge = null;

if (window.qt?.webChannelTransport) {
  const script = document.createElement("script");
  script.src = "qrc:///qtwebchannel/qwebchannel.js";
  script.onload = () => {
    new window.QWebChannel(
      window.qt.webChannelTransport,
      channel => {
        nativeBridge = channel.objects.widgetBridge;
      }
    );
  };
  document.head.appendChild(script);
}
import React, { useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

import fractalLexicon from './fractal_lexicon.json';

const sonicCatalog = [
  {id: 'sonic-workshop', name: 'SONIC WORKSHOP', category: 'Music Theory', description: 'Living Music Book, Scale Explorer, Chord Forge, metronome, rudiments, and Interval Ear Trainer.'},
  {id: 'polyrhythm-reactor', name: 'POLYRHYTHM REACTOR', category: 'Rhythm Laboratory', description: 'Standalone interactive polyrhythm dial and percussion engine.'}
];
const modules = [
  { id: "TB", name: "TOKENBRIDGES", icon: "⌁",
    description: "Spawn bridges between tools and environments." },
  { id: "MW", name: "MINI WIDGETS", icon: "◈",
    description: "Small tools for delightfully specific problems." },
  { id: "WR", name: "WIDGET REGISTRY", icon: "▦",
    description: "Explore installed modules and their states." },
  { id: "SW", name: "MUSIC WIDGETS", icon: "♫", description: "Interactive musical instruments and theory laboratories." },
  { id: "PS", name: "POWERSHELL WIDGETS", icon: ">_", description: "Discover PowerShell profile functions without executing them." },
  { id: "ST", name: "SETTINGS", icon: "⚙",
    description: "Customize the environment and its behavior." }
];

function App() {
  const [selectedFractal, setSelectedFractal] = useState('beacon');
  const [seed, setSeed] = useState(null);
  const [rotation, setRotation] = useState(180);
  const [inverted, setInverted] = useState(true);
  const [logs, setLogs] = useState([]);
  const [seconds, setSeconds] = useState(0);
  const [page, setPage] = useState('home');
  const [psFunctions, setPsFunctions] = useState([]);
  const [psStatus, setPsStatus] = useState('Ready to inspect local profiles.');
  const [category, setCategory] = useState('All Widgets');
  const [query, setQuery] = useState('');
  const [spawned, setSpawned] = useState([]);



  function log(message) {
    const time = new Date().toLocaleTimeString();
    setLogs(old => [...old.slice(-79), {time, message}]);
  }

  useEffect(() => {
    const timer = setInterval(() => setSeconds(s => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    log("Chromatic reactor initialized.");
    log("React control engine online.");
    log("Five modules registered.");
  }, []);

  function rewarp() {
    const next = Math.floor(Math.random() * 360);
    setSeed(next);
    log(`Chromatic field regenerated // seed ${next}°`);
  }

  function activate(module) {
    if (module.id === "PS") {
      setPage("powershell");
      setPsStatus("Requesting read-only discovery...");
      if (!nativeBridge || !nativeBridge.discoverPowerShell) {
        setPsStatus("Native PowerShell bridge not ready. Try reopening this module.");
      } else {
        nativeBridge.discoverPowerShell();
      }
      return;
    }
    if (module.id === "SW") {
      setPage("music");
      log("SONIC WORKSHOP // music library opened");
      return;
    }    if (module.id === "MW") {
      setPage("library");
      log("MINI WIDGETS // library opened");
      return;
    }
    log(`${module.name} // placeholder activated`);
  }

  useEffect(() => {
    let active = true;
    let attached = null;
    const timer = setInterval(() => {
      if (!nativeBridge || !nativeBridge.powerShellDiscovered || attached) return;
      attached = nativeBridge;
      attached.powerShellDiscovered.connect(payload => {
        if (!active) return;
        try {
          const result = JSON.parse(payload);
          if (!result.ok) throw new Error(result.error || 'Discovery failed');
          setPsFunctions(result.functions || []);
          setPsStatus(`${(result.functions || []).length} function definitions discovered (AST only).`);
        } catch (error) {
          setPsStatus(`Discovery error: ${error.message}`);
        }
      });
      clearInterval(timer);
    }, 250);
    return () => { active = false; clearInterval(timer); };
  }, []);

  function spawnMini(id) {
    if (!nativeBridge) {
      log("Native widget bridge not ready.");
      return;
    }
    nativeBridge.spawn(id);
    setSpawned(old => [...old, {id, serial: Date.now() + Math.random()}]);
    log(`MINI WIDGET // ${id} spawn requested`);
  }

  const reactorLive = seed !== null;
  const hue = ((seed ?? 32) + rotation) % 360;

  const reactorColors = [
    `hsl(${hue} 90% 59%)`,
    `hsl(${(hue + 120) % 360} 85% 57%)`,
    `hsl(${(hue + 240) % 360} 82% 59%)`
  ];

  const theme = {
    "--hue": hue,
    "--secondary-hue": (hue + 120) % 360,
    "--complement-hue": (hue + 240) % 360,
    "--reactor-a": reactorColors[0],
    "--reactor-b": reactorColors[1],
    "--reactor-c": reactorColors[2],
    "--reactor-bg": inverted ? "#08090c" : "#18151a"
  };

  return (
    <div className={`${inverted ? "app inverted" : "app"}${reactorLive ? " reactor-live" : ""}`} style={theme}>
      <div className="warp-field" aria-hidden="true">
        <div className="warp-orb orb-one"/>
        <div className="warp-orb orb-two"/>
        <div className="warp-grid"/>
      </div>

      <main className="shell">
        <header className="topline">
          <span><i className="pulse"/> REACTOR ONLINE</span>
          <span>RING 0.8 // POCKET WEATHER</span>
        </header>

        <nav className="ww-nav">
          <button className={page === 'home' ? 'selected' : ''} onClick={() => setPage('home')}>HOME</button>
          <button className={page === 'library' ? 'selected' : ''} onClick={() => setPage('library')}>MINI WIDGETS</button>
          <button className={page === 'running' ? 'selected' : ''} onClick={() => setPage('running')}>RUNNING WIDGETS</button>
          <button className={page === 'music' ? 'selected' : ''} onClick={() => setPage('music')}>MUSIC WIDGETS</button>
          <button className={page === 'powershell' ? 'selected' : ''} onClick={() => activate(modules.find(m => m.id === "PS"))}>&#9889; POWERSHELL</button>
          <button className={page === 'fractal' ? 'selected' : ''} onClick={() => setPage('fractal')}>&#127744; FRACTAL WIDGETS</button>
        </nav>
        {page === 'home' && <>
        <div className="hero">
          <div className="eyebrow">MODULAR DESKTOP LABORATORY</div>
          <h1 className="chaos-title" key={seed ?? "infernal"}>
  <span className="chaos-word">WIDGET</span>
  <span className="chaos-wall">
    <span className="chaos-underscore">_</span>WALL
  </span>
</h1>
          <p>Small tools. Strange ideas. Infinite combinations.</p>
        </div>

        <div className="section">
          <span>01 / MODULE CONTROL</span>
        </div>

        <div className="grid">
          {modules.map((module, i) => (
            <article className="card" key={module.id}>
              <div className="card-top">
                <div className="module-icon">{module.icon}</div>
                <span className="module-id">0{i+1} / 06</span>
              </div>
              <h2>{module.name}</h2>
              <p>{module.description}</p>
              <button onClick={() => activate(module)}>
                INITIALIZE <span>↗</span>
              </button>
            </article>
          ))}
        </div>

<div className="section">
          <span>02 / CHROMATIC ENGINE</span>
        </div>

        <section className="engine">
          <div className="engine-header">
            <div>
              <h2>COLOR REACTOR</h2>
              <p>Procedural hue rotation and complementary inversion.</p>
            </div>
            <button className="primary" onClick={rewarp}>
              ⟳ REWARP
            </button>
          </div>

          <div className="color-strip">
            {reactorColors.map((color,i) => (
              <div key={i} style={{background:color}}>
                <span>{[hue,(hue+120)%360,(hue+240)%360][i]}°</span>
              </div>
            ))}
          </div>

          <div className="controls">
            <label>
              ROTATION <strong>{rotation}°</strong>
              <input type="range" min="0" max="359"
                value={rotation}
                onChange={e => setRotation(Number(e.target.value))}/>
            </label>

            <label className="toggle">
              <input type="checkbox" checked={inverted}
                onChange={e => {
                  setInverted(e.target.checked);
                  log("Palette inversion toggled.");
                }}/>
              INVERTED PALETTE
            </label>
          </div>
        </section>

        <div className="section">
          <span>03 / ACTIVITY STREAM</span>
        </div>

        <div className="terminal" role="log" aria-live="polite">
          {logs.map((entry,i) => (
            <div className="log" key={i}>
              <span>[{entry.time}]</span> {entry.message}
            </div>
          ))}
        </div>

        </>}
        {page === 'library' && <section className="ww-library">
          <div className="ww-pagehead">
            <div><div className="eyebrow">GADGET RESURRECTION / LIBRARY</div><h1>MINI <span>WIDGETS</span></h1>
              <p>Browse the classics. Spawn native Windows overlays.</p></div>
            <div className="ww-count">{libraryCatalog.length} CATALOGED / {libraryCatalog.filter(w => w.ready).length} READY</div>
          </div>
          <input className="ww-search" placeholder="SEARCH WIDGETS..." value={query} onChange={e => setQuery(e.target.value)}/>
          <div className="ww-categories">
            {libraryCategories.map(c => <button key={c} className={category === c ? 'selected' : ''} onClick={() => setCategory(c)}>{c}</button>)}
          </div>
          <div className="ww-catalog">
            {libraryCatalog.filter(w => (category === 'All Widgets' || w.category === category) &&
              (w.name + ' ' + w.description).toLowerCase().includes(query.toLowerCase())).map(w =>
              <article className="ww-widget" key={w.id}>
                <div className="ww-widget-top"><span>{w.category}</span><b className={w.ready ? 'ww-ready' : 'ww-planned'}>{w.ready ? 'READY' : 'PLANNED'}</b></div>
                <h2>{w.name}</h2><p>{w.description}</p>
                <button disabled={!w.ready} onClick={() => spawnMini(w.id)}>{w.ready ? '+ SPAWN OVERLAY' : 'AWAITING ENGINE'}</button>
              </article>)}
          </div>
        </section>}
        {page === 'music' && <section className="ww-library">
          <div className="ww-pagehead"><div><div className="eyebrow">WIDGET_WALL / SONIC WORKSHOP</div>
            <h1>MUSIC <span>WIDGETS</span></h1><p>Interactive theory, rhythm experiments, and ear training. Launch each in its own desktop window.</p></div>
            <div className="ww-count">02 INSTRUMENTS / NATIVE WINDOWS</div></div>
          <div className="ww-catalog">{sonicCatalog.map(w => <article className="ww-widget" key={w.id}>
            <div className="ww-widget-top"><span>{w.category}</span><b className="ww-ready">READY</b></div>
            <h2>{w.name}</h2><p>{w.description}</p>
            <button onClick={() => spawnMini(w.id)}>+ LAUNCH INSTRUMENT</button>
          </article>)}</div>
        </section>}        {page === 'running' && <section className="ww-library">
          <div className="eyebrow">OVERLAY ACTIVITY</div><h1>RUNNING <span>WIDGETS</span></h1>
          <p>This session has requested {spawned.length} overlays. Closing an overlay directly does not yet sync this list.</p>
          <div className="ww-catalog">{spawned.map((w,i) => <article className="ww-widget" key={w.serial}>
            <div className="ww-widget-top"><span>SPAWN #{i+1}</span><b className="ww-ready">REQUESTED</b></div>
            <h2>{(libraryCatalog.concat(sonicCatalog)).find(item => item.id === w.id)?.name || w.id}</h2>
            <p>Native window created by the Python bridge.</p>
            <button onClick={() => spawnMini(w.id)}>+ SPAWN ANOTHER</button>
          </article>)}</div>
          {spawned.length === 0 && <div className="ww-empty">No overlays spawned from this session yet.</div>}
        </section>}
        {page === 'powershell' && (
          <section className="mini-launcher">
            <div className="mini-heading">
              <h2>POWERSHELL WIDGETS // FUNCTION REGISTRY</h2>
              <button onClick={() => setPage('home')}>BACK</button>
            </div>
            <p>{psStatus}</p>
            <p>Read-only discovery. No functions are executed.</p>
            <div className="mini-grid">
              {psFunctions.map((fn, i) => (
                <div className="mini-tile" key={`${fn.source}:${fn.name}:${i}`}>
                  <h3>{fn.name}</h3>
                  <p>{fn.parameters.length ? `Parameters: ${fn.parameters.join(', ')}` : 'No declared parameters'}</p>
                  <p>{fn.engine} // line {fn.line}</p>
                </div>
              ))}
            </div>
          </section>
        )}
        {page === 'fractal' && (
          <section className="mini-launcher">
            <div className="mini-heading">
              <h2>FRACTAL WIDGETS // LEXICON</h2>
              <button onClick={() => setPage('home')}>BACK</button>
            </div>
            <p>Explore the abstracted building blocks behind the workflow. These are explanatory concepts, not executable commands.</p>
            <div className="mini-grid">
              {fractalLexicon.map(item => (
                <button key={item.id} type="button" className="mini-tile"
                  onClick={() => setSelectedFractal(item.id)}
                  style={{cursor:'pointer', textAlign:'left', borderColor:selectedFractal === item.id ? '#f0a45a' : undefined}}>
                  <h3>{item.icon} {item.name}</h3>
                  <p>{item.short}</p>
                  <p>{item.category} // {item.status}</p>
                </button>
              ))}
            </div>
            {fractalLexicon.filter(item => item.id === selectedFractal).map(item => (
              <div key={item.id} className="mini-tile" style={{marginTop:20, padding:20}}>
                <h2>{item.icon} {item.name}</h2>
                <p>{item.description}</p>
                <h3>EXAMPLE APPLICATION</h3>
                <p>{item.example}</p>
                <p>{item.category} // {item.status} // READ ONLY</p>
              </div>
            ))}
          </section>
        )}
        <div className="bottom-space"/>
      </main>

      <footer className="statusbar">
        <span><i className="pulse"/> SYSTEM ACTIVE</span>
        <span>MODULES: 06</span>
        <span>HUE: {hue}°</span>
        <span>UPTIME: {Math.floor(seconds/60)}m {seconds%60}s</span>
        <span>RING 0.8</span>
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App/>);
