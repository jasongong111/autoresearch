import { HashRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import RunConfigurator from "./pages/RunConfigurator";
import RunManager from "./pages/RunManager";

export default function App() {
  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/runs" element={<RunManager />} />
          <Route path="/runs/new" element={<RunConfigurator />} />
        </Routes>
      </Layout>
    </HashRouter>
  );
}
