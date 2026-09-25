"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, Clipboard, Database, ExternalLink, Lock, Mail, RefreshCw, Save, Server, Settings as SettingsIcon, Shield, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function SettingsPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<{ status: string; env: string; database: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [emailPrivacyLocked, setEmailPrivacyLocked] = useState(user?.email_privacy_locked ?? true);
  const [emailConfigured, setEmailConfigured] = useState(false);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [emailAddress, setEmailAddress] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [imapHost, setImapHost] = useState("imap.gmail.com");
  const [imapPort, setImapPort] = useState(993);
  const [smtpHost, setSmtpHost] = useState("smtp.gmail.com");
  const [smtpPort, setSmtpPort] = useState(587);
  const [emailBusy, setEmailBusy] = useState(false);
  const [emailMessage, setEmailMessage] = useState("");
  const [whatsappStatus, setWhatsappStatus] = useState<{ configured: boolean; connected: boolean; status: string; accounts: Array<{ phone_number?: string; display_name?: string; status: string }> } | null>(null);
  const [whatsappBusy, setWhatsappBusy] = useState(false);
  const [whatsappSetupOpen, setWhatsappSetupOpen] = useState(true);
  const [waPhoneNumberId, setWaPhoneNumberId] = useState("");
  const [waAccessToken, setWaAccessToken] = useState("");
  const [waAppSecret, setWaAppSecret] = useState("");
  const [waVerifyToken, setWaVerifyToken] = useState("");
  const [waPublicUrl, setWaPublicUrl] = useState("");
  const [waConfigMessage, setWaConfigMessage] = useState("");

  async function checkBackendHealth() {
    setLoading(true);
    try {
      setHealth(await api.checkHealth());
    } catch {
      setHealth({ status: "disconnected", env: "error", database: "unknown" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    checkBackendHealth();
    if (user) setEmailPrivacyLocked(user.email_privacy_locked ?? true);
    api.getMyEmailSettings().then((settings) => {
      setEmailConfigured(settings.configured);
      setEmailEnabled(settings.enabled);
      setEmailAddress(settings.email_address || "");
      setImapHost(settings.imap_host || "imap.gmail.com");
      setImapPort(settings.imap_port || 993);
      setSmtpHost(settings.smtp_host || "smtp.gmail.com");
      setSmtpPort(settings.smtp_port || 587);
    }).catch(() => {});
    api.getWhatsAppStatus().then(setWhatsappStatus).catch(() => setWhatsappStatus(null));
    api.getWhatsAppConfig().then((config) => { setWaPhoneNumberId(config.phone_number_id || ""); setWaPublicUrl(config.public_api_url || ""); }).catch(() => {});
  }, [user]);

  async function saveSettings() {
    setSaving(true);
    try {
      await api.updateMySettings({ email_privacy_locked: emailPrivacyLocked });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      alert(`Failed to save privacy settings: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  async function saveEmailConnection() {
    setEmailBusy(true);
    setEmailMessage("");
    try {
      const result = await api.saveMyEmailSettings({ enabled: emailEnabled, email_address: emailAddress, password: emailPassword, imap_host: imapHost, imap_port: imapPort, smtp_host: smtpHost, smtp_port: smtpPort });
      setEmailConfigured(result.configured);
      setEmailPassword("");
      setEmailMessage("Email details saved securely. Test the connection before syncing.");
    } catch (err: any) {
      setEmailMessage(err.message);
    } finally {
      setEmailBusy(false);
    }
  }

  async function testEmailConnection() {
    setEmailBusy(true);
    setEmailMessage("");
    try {
      await api.testMyEmailSettings();
      setEmailMessage("Email connection verified. Your inbox is ready to sync.");
    } catch (err: any) {
      setEmailMessage(err.message);
    } finally {
      setEmailBusy(false);
    }
  }

  async function refreshWhatsAppStatus() {
    try { setWhatsappStatus(await api.getWhatsAppStatus()); } catch { setWhatsappStatus(null); }
  }

  async function configureWhatsAppWebhooks() {
    setWhatsappBusy(true);
    try {
      await api.configureWhatsAppWebhooks();
      await refreshWhatsAppStatus();
      alert("Meta webhook details are ready. Add the callback URL and verify token in Meta Developers.");
    } catch (err: any) {
      alert(err.message);
    } finally {
      setWhatsappBusy(false);
    }
  }

  async function syncWhatsApp() {
    setWhatsappBusy(true);
    try {
      const result = await api.syncWhatsApp();
      alert(`Meta account checked. Existing conversations will appear when new webhook messages arrive.`);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setWhatsappBusy(false);
    }
  }

  async function saveWhatsAppConfiguration(event: React.FormEvent) {
    event.preventDefault();
    setWhatsappBusy(true);
    setWaConfigMessage("");
    try {
      await api.saveWhatsAppConfig({ phone_number_id: waPhoneNumberId, access_token: waAccessToken, app_secret: waAppSecret, verify_token: waVerifyToken, public_api_url: waPublicUrl });
      setWaAccessToken(""); setWaAppSecret("");
      setWaConfigMessage("Saved securely. Now configure the Meta webhook using the URL below.");
      await refreshWhatsAppStatus();
    } catch (err: any) { setWaConfigMessage(err.message); }
    finally { setWhatsappBusy(false); }
  }

  return (
    <div className="space-y-8 max-w-5xl animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-emerald-400" /> Platform Settings
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-slate-900 border border-slate-800 text-emerald-400">Role: {user?.role || "MEMBER"}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Manage privacy and monitor the Nexus platform.</p>
        </div>
        <button onClick={saveSettings} disabled={saving} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 disabled:opacity-50">
          {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Settings
        </button>
      </div>

      {saveSuccess && <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium flex items-center gap-2"><CheckCircle2 className="w-4 h-4" /> Privacy settings saved.</div>}

      <section className="rounded-2xl p-6 border border-slate-800 space-y-5 bg-slate-900/80">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3"><div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400"><ShieldCheck className="w-6 h-6" /></div><div><h2 className="text-base font-bold text-white">Personal Data & Email Privacy</h2><p className="text-xs text-slate-400 mt-1">Keep personal emails, drafts, and action plans private to your account.</p></div></div>
          <span className="px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> Strict Isolation</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
          <div><span className="font-semibold text-white text-sm flex items-center gap-2"><Lock className="w-4 h-4 text-purple-400" /> Lock personal inbox to my user ID</span><span className="text-xs text-slate-400 block mt-1 max-w-2xl">Other users and their AI sessions cannot view or query your personal email data.</span></div>
          <button type="button" onClick={() => setEmailPrivacyLocked(!emailPrivacyLocked)} aria-label="Toggle personal inbox privacy" className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors ${emailPrivacyLocked ? "bg-purple-600" : "bg-slate-800"}`}><span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${emailPrivacyLocked ? "translate-x-5" : "translate-x-0"}`} /></button>
        </div>
      </section>

      <section className="rounded-2xl p-6 border border-slate-800 space-y-5 bg-slate-900/80">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3"><div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400"><Mail className="w-6 h-6" /></div><div><h2 className="text-base font-bold text-white">Email Connection</h2><p className="text-xs text-slate-400 mt-1">Use your own mailbox details. Credentials are encrypted on the server and never returned to the browser.</p></div></div>
          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${emailConfigured ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30" : "text-slate-400 bg-slate-800 border-slate-700"}`}>{emailConfigured ? "Configured" : "Not configured"}</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="text-xs text-slate-300">Email address<input value={emailAddress} onChange={(e) => setEmailAddress(e.target.value)} type="email" placeholder="you@example.com" className="mt-1 w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-cyan-500" /></label>
          <label className="text-xs text-slate-300">App password<input value={emailPassword} onChange={(e) => setEmailPassword(e.target.value)} type="password" placeholder={emailConfigured ? "Enter a new password to replace it" : "Provider app password"} className="mt-1 w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-cyan-500" /></label>
          <label className="text-xs text-slate-300">IMAP host<input value={imapHost} onChange={(e) => setImapHost(e.target.value)} className="mt-1 w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-cyan-500" /></label>
          <label className="text-xs text-slate-300">IMAP port<input value={imapPort} onChange={(e) => setImapPort(Number(e.target.value))} type="number" className="mt-1 w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-cyan-500" /></label>
          <label className="text-xs text-slate-300">SMTP host<input value={smtpHost} onChange={(e) => setSmtpHost(e.target.value)} className="mt-1 w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-cyan-500" /></label>
          <label className="text-xs text-slate-300">SMTP port<input value={smtpPort} onChange={(e) => setSmtpPort(Number(e.target.value))} type="number" className="mt-1 w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-cyan-500" /></label>
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-300"><input type="checkbox" checked={emailEnabled} onChange={(e) => setEmailEnabled(e.target.checked)} /> Enable inbox sync and sending for this account</label>
        <div className="flex flex-wrap items-center gap-3"><button onClick={saveEmailConnection} disabled={emailBusy || !emailAddress || !emailPassword} className="px-4 py-2 rounded-lg bg-cyan-500 text-slate-950 text-xs font-semibold disabled:opacity-40">{emailBusy ? "Working..." : "Save email connection"}</button><button onClick={testEmailConnection} disabled={emailBusy || !emailConfigured} className="px-4 py-2 rounded-lg border border-slate-700 text-slate-200 text-xs font-semibold disabled:opacity-40">Test connection</button>{emailMessage && <span className="text-xs text-slate-300">{emailMessage}</span>}</div>
      </section>

      {(user?.role === "ADMIN" || user?.role === "MANAGER") && <section className="rounded-2xl p-6 border border-slate-800 space-y-4 bg-slate-900/80">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4"><div><h2 className="text-base font-bold text-white">WhatsApp Integration · Meta Cloud API</h2><p className="text-xs text-slate-400 mt-1">Provider credentials stay in the backend environment. This panel exposes status only.</p></div><span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${whatsappStatus?.connected ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30" : "text-slate-400 bg-slate-800 border-slate-700"}`}>{whatsappStatus?.connected ? "Connected" : "Not Connected"}</span></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs"><div className="bg-slate-950/70 rounded-xl border border-slate-800 p-3"><span className="text-slate-500 uppercase font-bold">Configuration</span><p className="text-white mt-1">{whatsappStatus?.configured ? "API credentials detected" : "Server credentials required"}</p></div><div className="bg-slate-950/70 rounded-xl border border-slate-800 p-3"><span className="text-slate-500 uppercase font-bold">Accounts</span>{whatsappStatus?.accounts.length ? whatsappStatus.accounts.map((account, index) => <p key={index} className="text-slate-200 mt-1">{account.phone_number || account.display_name || "WhatsApp account"} · {account.status}</p>) : <p className="text-slate-400 mt-1">No verified accounts</p>}</div><div className="bg-slate-950/70 rounded-xl border border-slate-800 p-3"><span className="text-slate-500 uppercase font-bold">Status</span><p className="text-slate-200 mt-1">{whatsappStatus?.status === "not_configured" ? "Setup required" : whatsappStatus?.status || "Checking"}</p></div></div>
        <div className="flex flex-wrap gap-3"><button onClick={refreshWhatsAppStatus} className="px-4 py-2 rounded-lg border border-slate-700 text-slate-200 text-xs font-semibold">Check Meta connection</button><button onClick={configureWhatsAppWebhooks} disabled={whatsappBusy || !whatsappStatus?.configured} className="px-4 py-2 rounded-lg border border-cyan-500/40 text-cyan-300 text-xs font-semibold disabled:opacity-40">Show webhook details</button><button onClick={syncWhatsApp} disabled={whatsappBusy || !whatsappStatus?.connected} className="px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 text-xs font-semibold disabled:opacity-40">Check phone account</button></div>
        <form onSubmit={saveWhatsAppConfiguration} className="border-t border-slate-800 pt-4 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-white">Administrator setup</p>
              <p className="text-xs text-slate-400">Enter these values from Meta Developers. Secrets are encrypted by Nexus and never displayed again.</p>
            </div>
          </div>

          <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 text-xs text-slate-300">
            <p className="font-semibold text-white">Easy setup flow</p>
            <ol className="mt-2 space-y-2 list-decimal list-inside text-slate-300">
              <li>Open Meta Developers and create a WhatsApp Business app.</li>
              <li>Copy the WhatsApp Phone Number ID and create a permanent access token.</li>
              <li>Paste the values below, set a real public HTTPS URL, and save.</li>
              <li>Click “Check Meta connection” and then configure the webhook in Meta.</li>
            </ol>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="field-label">
              Meta Phone Number ID
              <input required value={waPhoneNumberId} onChange={(e) => setWaPhoneNumberId(e.target.value)} placeholder="123456789012345" className="input-field" />
            </label>

            <label className="field-label">
              Meta access token
              <input required value={waAccessToken} onChange={(e) => setWaAccessToken(e.target.value)} type="password" placeholder="EAAB..." className="input-field" />
            </label>

            <label className="field-label">
              Meta app secret
              <input value={waAppSecret} onChange={(e) => setWaAppSecret(e.target.value)} type="password" placeholder="App secret from Meta" className="input-field" />
            </label>

            <label className="field-label">
              Private webhook verify token
              <input required value={waVerifyToken} onChange={(e) => setWaVerifyToken(e.target.value)} placeholder="Create your own secret token" className="input-field" />
            </label>

            <label className="field-label md:col-span-2">
              Public HTTPS URL
              <input required value={waPublicUrl} onChange={(e) => setWaPublicUrl(e.target.value)} placeholder="https://api.example.com" className="input-field" />
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" disabled={whatsappBusy} className="px-4 py-2 rounded-lg bg-cyan-500 text-slate-950 text-xs font-semibold disabled:opacity-50">
              {whatsappBusy ? "Saving securely..." : "Save Meta connection"}
            </button>
            {waConfigMessage && <p className="text-xs text-slate-300">{waConfigMessage}</p>}
          </div>
        </form>
        <div className="border-t border-slate-800 pt-4">
          <button type="button" onClick={() => setWhatsappSetupOpen(!whatsappSetupOpen)} className="text-sm font-semibold text-cyan-300 hover:text-cyan-200">
            {whatsappSetupOpen ? "Hide setup guide" : "Show setup guide"}
          </button>
          {whatsappSetupOpen && (
            <div className="mt-4 space-y-4 text-xs text-slate-300">
              <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                <p className="font-semibold text-white">Why there are no editable token fields here</p>
                <p className="mt-1 text-slate-400">Only administrators can save Meta credentials. Use the Administrator setup form above; Nexus encrypts secrets on the backend and never shows them again.</p>
              </div>
              <ol className="space-y-3 list-decimal list-inside">
                <li><span className="font-semibold text-white">Create the Meta app:</span> open <a href="https://developers.facebook.com/apps" target="_blank" rel="noreferrer" className="text-cyan-300 inline-flex items-center gap-1">Meta Developers <ExternalLink className="w-3 h-3" /></a>, create a Business app, and add WhatsApp.</li>
                <li><span className="font-semibold text-white">Copy the API values:</span> from WhatsApp &gt; API Setup, copy the Phone Number ID and create a production System User access token.</li>
                <li><span className="font-semibold text-white">Save the connection:</span> complete the Administrator setup form above. The public URL must be a real HTTPS address reachable by Meta.</li>
                <li><span className="font-semibold text-white">Configure Meta Webhooks:</span> use the webhook URL returned by Nexus after saving, enter the same verify token, and subscribe to <span className="font-mono text-cyan-300">messages</span>.</li>
                <li><span className="font-semibold text-white">Restart and check:</span> restart the backend, return here, and select Check Meta connection. Send a WhatsApp message to the business number to create the first inbox conversation.</li>
              </ol>
              <div className="flex items-center gap-2 text-slate-500"><Clipboard className="w-3.5 h-3.5" />Never paste access tokens into chat, screenshots, or frontend code.</div>
            </div>
          )}
        </div>
      </section>}

      <section className="rounded-2xl p-6 border border-slate-800 space-y-4 bg-slate-900/80">
        <div className="flex items-center justify-between"><h2 className="text-base font-bold text-white flex items-center gap-2"><Server className="w-5 h-5 text-emerald-400" /> System Diagnostics</h2><button onClick={checkBackendHealth} disabled={loading} className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-xs font-semibold text-slate-300 flex items-center gap-1.5"><RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} /> Refresh</button></div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800"><span className="text-[10px] uppercase font-bold text-slate-500 block">System Status</span><span className="font-semibold text-emerald-400 mt-1 flex items-center gap-1.5 text-sm"><CheckCircle2 className="w-4 h-4" /> {health?.status ? health.status.toUpperCase() : "OPERATIONAL"}</span></div>
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800"><span className="text-[10px] uppercase font-bold text-slate-500 block">Environment</span><span className="font-mono text-slate-200 mt-1 block text-sm">{health?.env || "development"}</span></div>
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800"><span className="text-[10px] uppercase font-bold text-slate-500 block">Database</span><span className="font-mono text-slate-200 mt-1 block text-sm"><Database className="w-3.5 h-3.5 inline mr-1" />{health?.database || "Unknown"}</span></div>
        </div>
      </section>
    </div>
  );
}
