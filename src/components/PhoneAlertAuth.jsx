import { useState } from "react";
import { auth } from "../firebase";
import { RecaptchaVerifier, signInWithPhoneNumber } from "firebase/auth";

export default function PhoneAlertAuth() {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [confirmationResult, setConfirmationResult] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);



  const sendCode = async () => {
    setStatus("");
    setLoading(true);
    try {
      // Always create a new RecaptchaVerifier instance on button click
      const appVerifier = new RecaptchaVerifier(
        "recaptcha-container",
        { size: "normal" },
        auth
      );
      const result = await signInWithPhoneNumber(auth, phone, appVerifier);
      setConfirmationResult(result);
      setStatus("Code sent! Please enter the verification code.");
    } catch (err) {
      setStatus(err.message || "Failed to send code.");
    }
    setLoading(false);
  };

  const verifyCode = async () => {
    setStatus("");
    if (!confirmationResult) {
      setStatus("Please send the code to your phone first.");
      return;
    }
    setLoading(true);
    try {
      await confirmationResult.confirm(code);
      setStatus("Phone verified. You are subscribed to outage alerts.");
    } catch (err) {
      setStatus(err.message || "Verification failed.");
    }
    setLoading(false);
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
      <div id="recaptcha-container" style={{ marginBottom: 10 }}></div>
      <h3 style={{ margin: "0 0 8px", color: "#fff" }}>Phone Alert Signup</h3>
      <div style={{ fontSize: 14, marginBottom: 12, color: "#ccc" }}>
        Verify your phone number to receive outage alerts.
      </div>
      <input
        type="tel"
        placeholder="+15555555555"
        value={phone}
        onChange={e => setPhone(e.target.value)}
        style={{ width: "100%", marginBottom: 8, padding: 8, fontSize: 15, background: "#23262f", color: "#fff", border: "1px solid #444" }}
        disabled={loading}
      />
      <button
        onClick={sendCode}
        disabled={loading || !phone}
        style={{ width: "100%", marginBottom: 10, padding: 8, fontSize: 15, background: "#23262f", color: "#fff", border: "1px solid #444" }}
      >
        Send Code
      </button>
      <input
        type="text"
        placeholder="Verification code"
        value={code}
        onChange={e => setCode(e.target.value)}
        style={{ width: "100%", marginBottom: 8, padding: 8, fontSize: 15, background: "#23262f", color: "#fff", border: "1px solid #444" }}
        disabled={loading}
      />
      <button
        onClick={verifyCode}
        disabled={loading || !code}
        style={{ width: "100%", marginBottom: 10, padding: 8, fontSize: 15, background: "#23262f", color: "#fff", border: "1px solid #444" }}
      >
        Verify &amp; Subscribe
      </button>
      <div style={{ minHeight: 24, fontSize: 14, color: "#fff" }}>{status}</div>
      <div style={{ fontSize: 12, color: "#aaa", marginTop: 8 }}>
        Demo test number: +15555555555 | Code: 123456
      </div>
    </div>
  );
}
