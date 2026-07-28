import { NavLink, Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <NavLink to="/" className="brand">
          Trascrivi <span className="brand-accent">Reel</span>
        </NavLink>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <nav className="tabbar">
        <NavLink to="/" end className="tab">
          <span className="tab-icon">✎</span>
          <span>Home</span>
        </NavLink>
        <NavLink to="/archive" className="tab">
          <span className="tab-icon">▤</span>
          <span>Archivio</span>
        </NavLink>
        <NavLink to="/settings" className="tab">
          <span className="tab-icon">⚙</span>
          <span>Brand</span>
        </NavLink>
      </nav>
    </div>
  );
}
