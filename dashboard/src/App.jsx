import { useEffect, useState } from "react";
import "./App.css";

const DASHBOARD_API = "http://127.0.0.1:8000/dashboard";
const BACKEND_API = "http://127.0.0.1:8000";

export default function App() {
  
  const [data, setData] = useState(null);

  const [assetId, setAssetId] = useState("");

  const [newAssetId, setNewAssetId] = useState("");
  const [newAssetType, setNewAssetType] = useState("");

  const [zoneStats, setZoneStats] = useState([]);
 
  const [removeAssetId, setRemoveAssetId] = useState("");

  async function loadDashboard() {
    const res = await fetch(DASHBOARD_API);
    const json = await res.json();
    setData(json);
  }

  async function loanAsset() {
    if (!assetId) return;
  
    try {
      const res = await fetch(`${BACKEND_API}/assets/${assetId}/loan`, {
        method: "POST",
      });
  
      const data = await res.json();
  
      if (!res.ok) {
        alert(data.detail || "Could not register loan");
        return;
      }
  
      setAssetId("");
      loadDashboard();
    } catch (error) {
      alert("Server error while registering loan");
    }
  }

  async function loadZoneStats() {
    const res = await fetch(`${BACKEND_API}/zones/stats`);
    const json = await res.json();
    setZoneStats(json);
  }

  async function returnAsset() {
    if (!assetId) return;
  
    try {
      const res = await fetch(`${BACKEND_API}/assets/${assetId}/return`, {
        method: "POST",
      });
  
      const data = await res.json();
  
      if (!res.ok) {
        alert(data.detail || "Could not register return");
        return;
      }
  
      setAssetId("");
      loadDashboard();
    } catch (error) {
      alert("Server error while registering return");
    }
  }

  async function createAsset() {
    if (!newAssetId || !newAssetType) {
      alert("Please enter both asset ID and asset type");
      return;
    }
    try {
      const res = await fetch(`${BACKEND_API}/assets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          asset_id: newAssetId.toUpperCase(),
          asset_type: newAssetType,
        }),
      });
      const data = await res.json();

      if (!res.ok) {
        alert(data.detail || "Could not create asset");
        return;
      }
      setNewAssetId("");
      setNewAssetType("");
      loadDashboard();
    } catch (error) {
      alert("Server error while creating asset");
    }
  }

  async function removeAsset() {
    if (!removeAssetId) {
      alert("Please enter an asset ID");
      return;
    }
  
    try {
      const res = await fetch(`${BACKEND_API}/assets/${removeAssetId.toUpperCase()}`, {
        method: "DELETE",
      });
  
      const data = await res.json();
  
      if (!res.ok) {
        alert(data.detail || "Could not remove asset");
        return;
      }
  
      setRemoveAssetId("");
      loadDashboard();
    } catch (error) {
      alert("Server error while removing asset");
    }
  }

  useEffect(() => {
    loadDashboard();
    loadZoneStats();
    const i = setInterval(loadDashboard, 5000);
    return () => clearInterval(i);
  }, []);

  if (!data) return <div>Loading dashboard...</div>;

  return (
    <div className="container">
      <h1>Hospital Asset Tracker</h1>
      <div className="manual-panel">
  <input
    placeholder="Remove Asset ID (ex: W001)"
    value={removeAssetId}
    onChange={(e) => setRemoveAssetId(e.target.value)}
  />

  <button className="remove-btn" onClick={removeAsset}>
    Delete Asset
  </button>
</div>

      <div className="manual-panel">
        <input
          placeholder="New Asset ID (ex: W001)"
          value={newAssetId}
          onChange={(e) => setNewAssetId(e.target.value)}
        />
         <input
          placeholder="Asset Type (ex: Wheelchair)"
          value={newAssetType}
          onChange={(e) => setNewAssetType(e.target.value)}
        />

        <button className="add-btn" onClick={createAsset}>
          Add Asset
          </button>
      </div>

      <div className="manual-panel">
        <input
          placeholder="Enter Asset ID (ex: W001)"
          value={assetId}
          onChange={(e) => setAssetId(e.target.value)}
        />

        <button className="loan-btn" onClick={loanAsset}>
          Register Loan
        </button>

        <button className="return-btn" onClick={returnAsset}>
          Register Return
        </button>
      </div>
      
      <div className="grid">
        <Section title="Available" items={data.available}/>
        <Section title="Loaned" items={data.loaned}/>
        <Section title="Not Returned" items={data.not_returned}/>
        <Section title="Prioritized" items={data.prioritized}/>
        <Section title="Unknown" items={data.unknown}/>
        
        <div className="section">
  <h2>Most Used Zones</h2>

  {zoneStats.map((zone) => (
    <div key={zone.zone_name} className="asset">
      <b>{zone.zone_name}</b>
      <div className="small">Visits: {zone.visits}</div>
    </div>
     ))}
     </div>
      </div>
    </div>
  );
}

function Section({ title, items,}) {
  return (
    <div className="section">
      <h2>{title} ({items.length})</h2>

      {items.map((asset) => (
        <div className="asset" key={asset.asset_id}>
          <b>{asset.asset_id}</b> — {asset.asset_type}

          <div className="small">
            Zone: {asset.current_zone_name}
          </div>

          <div className="small">
            Status: {asset.status}
          </div>

          <div className="small">
            Loan time: {asset.loan_duration_minutes ?? "-"} min
          </div>
        </div>
      ))}
    </div>
  );
}