import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Key, Save, ShieldCheck, Clock, ArrowLeft } from 'lucide-react'

export function Settings({ setCurrentView }) {
  const [apiKey, setApiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState(null);
  const [stats, setStats] = useState({ has_api_key: false, last_ai_usage: null });

  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Error fetching settings:", err);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async () => {
    if (!apiKey) return;
    setIsSaving(true);
    try {
      const response = await fetch('/api/v1/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gemini_api_key: apiKey })
      });
      if (response.ok) {
        setStatus({ type: 'success', message: 'API Key saved successfully!' });
        setApiKey('');
        fetchSettings();
      }
    } catch (err) {
      setStatus({ type: 'error', message: 'Failed to save key.' });
    } finally {
      setIsSaving(false);
      setTimeout(() => setStatus(null), 3000);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => setCurrentView('home')} className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Back to Dashboard
        </Button>
        <div className="px-3 py-1 bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-widest rounded-full">
          App Configuration
        </div>
      </div>

      <Card className="border-2 shadow-xl">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5 text-primary" />
            AI Intelligence Settings
          </CardTitle>
          <CardDescription>
            Configure your Gemini 3 Flash API key for Deep Audit functionality.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-bold flex items-center gap-2">
                Gemini API Key
                {stats.has_api_key && <ShieldCheck className="h-4 w-4 text-green-500" />}
              </label>
              <div className="flex gap-2">
                <Input 
                  type="password" 
                  placeholder={stats.has_api_key ? "••••••••••••••••" : "Paste your API key here..."}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="bg-muted/10"
                />
                <Button onClick={handleSave} disabled={isSaving || !apiKey}>
                  {isSaving ? <span className="animate-spin mr-2">◌</span> : <Save className="h-4 w-4 mr-2" />}
                  Save
                </Button>
              </div>
              <p className="text-[10px] text-muted-foreground italic">
                Your API key is stored locally on your machine and is never shared.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4">
              <div className="p-4 bg-primary/5 rounded-xl border border-primary/10 flex flex-col gap-1">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">AI Status</span>
                <span className="font-bold text-sm flex items-center gap-2">
                  {stats.has_api_key ? (
                    <><div className="w-2 h-2 rounded-full bg-green-500" /> Active</>
                  ) : (
                    <><div className="w-2 h-2 rounded-full bg-yellow-500" /> Not Configured</>
                  )}
                </span>
              </div>
              <div className="p-4 bg-primary/5 rounded-xl border border-primary/10 flex flex-col gap-1">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Last AI Usage</span>
                <span className="font-bold text-sm flex items-center gap-2">
                  <Clock className="h-3 w-3" />
                  {stats.last_ai_usage ? new Date(stats.last_ai_usage).toLocaleTimeString() : 'Never'}
                </span>
              </div>
            </div>
          </div>

          {status && (
            <div className={`p-3 rounded-lg text-sm font-medium ${status.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {status.message}
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card className="bg-muted/30 border-dashed">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <span className="text-primary font-bold">!</span>
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-sm">About the 12-Hour Cooldown</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                To keep your personal API usage balanced, Deep AI Audits are limited to one request every 12 hours. Standard audits remain unlimited and local.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
