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
    <div className="rounded-3xl border border-grid-border bg-grid-card p-6 shadow-xl">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
        Phone Alert Signup
      </h3>
      <p className="mt-1 text-xs text-slate-500">
        Enter your phone number and carrier to receive outage alerts via SMS.
      </p>
      <input
        type="tel"
        placeholder="e.g. 5551234567"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        className="mt-4 w-full rounded-xl border border-grid-border bg-slate-800/50 px-4 py-2.5 text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
      />
      <select
        value={carrier}
        onChange={(e) => setCarrier(e.target.value)}
        className="mt-3 w-full rounded-xl border border-grid-border bg-slate-800/50 px-4 py-2.5 text-slate-200 focus:border-cyan-500 focus:outline-none"
      >
        {Object.keys(CARRIER_GATEWAYS).map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <button
        onClick={subscribe}
        className="mt-4 w-full rounded-xl bg-cyan-600 px-4 py-2.5 font-medium text-white hover:bg-cyan-500 transition-colors"
      >
        Subscribe
      </button>
      <div className="mt-3 min-h-6 text-sm text-slate-300">{status}</div>
      <p className="mt-3 text-xs text-slate-500">
        Free SMS via carrier gateway. Not for production use.
      </p>
    </div>
  );
}
