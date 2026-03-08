import { useState } from "react";

const CARRIER_GATEWAYS = {
  "AT&T": "txt.att.net",
  "T-Mobile": "tmomail.net",
  "Verizon": "vtext.com",
  "Sprint": "messaging.sprintpcs.com",
  "Xfinity": "vtext.com",
  "Virgin Mobile": "vmobl.com",
  "Tracfone": "mmst5.tracfone.com",
  "Metro PCS": "mymetropcs.com",
  "Boost Mobile": "sms.myboostmobile.com",
  "Cricket": "sms.cricketwireless.net",
  "Republic Wireless": "text.republicwireless.com",
  "Google Fi": "msg.fi.google.com",
  "U.S. Cellular": "email.uscc.net"
};

export default function PhoneAlertSignup() {
  const [phone, setPhone] = useState("");
  const [carrier, setCarrier] = useState("AT&T");
  const [status, setStatus] = useState("");

  const subscribe = async () => {
    setStatus("Sending...");
    const email = `${phone.replace(/\D/g, "")}@${CARRIER_GATEWAYS[carrier]}`;
    try {
      const res = await fetch("/api/send-alert-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (data.success) {
        setStatus("You are subscribed to outage alerts!");
      } else {
        setStatus(data.error || "Failed to subscribe.");
      }
    } catch (err) {
      setStatus("Error sending alert.");
    }
  };

  return (
    <div style={{
      maxWidth: 340,
      margin: "24px auto",
      padding: 20,
      border: "1px solid #333",
      borderRadius: 8,
      background: "#181a20",
      boxShadow: "0 2px 8px #0008"
    }}>
      <h3 style={{ margin: "0 0 8px", color: "#fff" }}>Phone Alert Signup</h3>
      <div style={{ fontSize: 14, marginBottom: 12, color: "#ccc" }}>
        Enter your phone number and carrier to receive free SMS outage alerts.
      </div>
      <input
        type="tel"
        placeholder="e.g. 5551234567"
        value={phone}
        onChange={e => setPhone(e.target.value)}
        style={{ width: "100%", marginBottom: 8, padding: 8, fontSize: 15, background: "#23262f", color: "#fff", border: "1px solid #444" }}
      />
      <select
        value={carrier}
        onChange={e => setCarrier(e.target.value)}
        style={{ width: "100%", marginBottom: 8, padding: 8, fontSize: 15, background: "#23262f", color: "#fff", border: "1px solid #444" }}
      >
        {Object.keys(CARRIER_GATEWAYS).map(c => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <button
        onClick={subscribe}
        style={{ width: "100%", marginBottom: 10, padding: 8, fontSize: 15, background: "#23262f", color: "#fff", border: "1px solid #444" }}
      >
        Subscribe
      </button>
      <div style={{ minHeight: 24, fontSize: 14, color: "#fff" }}>{status}</div>
      <div style={{ fontSize: 12, color: "#aaa", marginTop: 8 }}>
        Free SMS via carrier gateway. Not for production use.
      </div>
    </div>
  );
}
