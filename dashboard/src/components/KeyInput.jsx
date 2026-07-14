import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Check, Eye, EyeOff, Key, Server } from 'lucide-react';

const CONFIG_PREFIX = 'OPENSHORTS_AI_V1:';

const encodeUtf8Base64 = (value) => {
    const bytes = new TextEncoder().encode(value);
    let binary = '';
    bytes.forEach((byte) => {
        binary += String.fromCharCode(byte);
    });
    return btoa(binary);
};

const decodeUtf8Base64 = (value) => {
    const binary = atob(value);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return new TextDecoder().decode(bytes);
};

const parseSavedValue = (savedKey) => {
    if (!savedKey || !savedKey.startsWith(CONFIG_PREFIX)) {
        return {
            provider: 'gemini',
            apiKey: savedKey || '',
            baseUrl: '',
            model: 'gemini-2.5-flash',
            temperature: '0.2',
            timeoutSeconds: '180',
            maxTokens: '4096',
        };
    }

    try {
        const raw = decodeUtf8Base64(savedKey.slice(CONFIG_PREFIX.length));
        const parsed = JSON.parse(raw);
        return {
            provider: parsed.provider || 'openai_compatible',
            apiKey: parsed.apiKey || '',
            baseUrl: parsed.baseUrl || '',
            model: parsed.model || 'auto',
            temperature: String(parsed.temperature ?? 0.2),
            timeoutSeconds: String(parsed.timeoutSeconds ?? 180),
            maxTokens: String(parsed.maxTokens ?? 4096),
        };
    } catch (error) {
        console.warn('Could not read saved custom AI settings. Resetting the form.');
        return {
            provider: 'openai_compatible',
            apiKey: '',
            baseUrl: '',
            model: 'auto',
            temperature: '0.2',
            timeoutSeconds: '180',
            maxTokens: '4096',
        };
    }
};

export default function KeyInput({ onKeySet, savedKey }) {
    const initial = useMemo(() => parseSavedValue(savedKey), [savedKey]);
    const [provider, setProvider] = useState(initial.provider);
    const [apiKey, setApiKey] = useState(initial.apiKey);
    const [baseUrl, setBaseUrl] = useState(initial.baseUrl);
    const [model, setModel] = useState(initial.model);
    const [temperature, setTemperature] = useState(initial.temperature);
    const [timeoutSeconds, setTimeoutSeconds] = useState(initial.timeoutSeconds);
    const [maxTokens, setMaxTokens] = useState(initial.maxTokens);
    const [isVisible, setIsVisible] = useState(false);
    const [isSaved, setIsSaved] = useState(!!savedKey);

    useEffect(() => {
        const parsed = parseSavedValue(savedKey);
        setProvider(parsed.provider);
        setApiKey(parsed.apiKey);
        setBaseUrl(parsed.baseUrl);
        setModel(parsed.model);
        setTemperature(parsed.temperature);
        setTimeoutSeconds(parsed.timeoutSeconds);
        setMaxTokens(parsed.maxTokens);
        setIsSaved(!!savedKey);
    }, [savedKey]);

    const isCustom = provider === 'openai_compatible';
    const canSave = apiKey.trim().length > 0
        && (!isCustom || (baseUrl.trim().length > 0 && model.trim().length > 0));

    const markDirty = () => setIsSaved(false);

    const handleProviderChange = (event) => {
        const nextProvider = event.target.value;
        setProvider(nextProvider);
        if (nextProvider === 'gemini' && model === 'auto') {
            setModel('gemini-2.5-flash');
        }
        if (nextProvider === 'openai_compatible' && model === 'gemini-2.5-flash') {
            setModel('auto');
        }
        markDirty();
    };

    const handleSave = () => {
        if (!canSave) return;

        if (!isCustom) {
            onKeySet(apiKey.trim());
            setIsSaved(true);
            return;
        }

        const config = {
            provider: 'openai_compatible',
            baseUrl: baseUrl.trim().replace(/\/+$/, ''),
            apiKey: apiKey.trim(),
            model: model.trim(),
            temperature: Number(temperature) || 0.2,
            timeoutSeconds: Number(timeoutSeconds) || 180,
            maxTokens: Number(maxTokens) || 4096,
        };

        const encoded = CONFIG_PREFIX + encodeUtf8Base64(JSON.stringify(config));
        onKeySet(encoded);
        setIsSaved(true);
    };

    return (
        <div className="bg-surface border border-white/5 rounded-2xl p-6 mb-8 animate-[fadeIn_0.5s_ease-out]">
            <div className="flex items-center justify-between gap-4 mb-5">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-accent/20 rounded-lg text-accent">
                        {isCustom ? <Server size={20} /> : <Key size={20} />}
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold">AI Provider</h2>
                        <p className="text-xs text-zinc-500">Used for automatic viral clip detection.</p>
                    </div>
                </div>
                <span className="text-[10px] uppercase tracking-wider px-2 py-1 rounded border border-white/10 text-zinc-400">
                    {isCustom ? 'Custom Router' : 'Gemini'}
                </span>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm text-zinc-400 mb-2">Provider</label>
                    <select
                        value={provider}
                        onChange={handleProviderChange}
                        className="input-field"
                    >
                        <option value="gemini">Google Gemini</option>
                        <option value="openai_compatible">OpenAI Compatible / Custom Endpoint</option>
                    </select>
                </div>

                {isCustom && (
                    <>
                        <div>
                            <label className="block text-sm text-zinc-400 mb-2">Base URL</label>
                            <input
                                type="text"
                                value={baseUrl}
                                onChange={(event) => {
                                    setBaseUrl(event.target.value);
                                    markDirty();
                                }}
                                placeholder="http://omniroute:20128/v1"
                                className="input-field font-mono"
                            />
                            <p className="mt-2 text-xs text-zinc-500">
                                The backend appends <code>/chat/completions</code>. From Docker, use the router service name or <code>host.docker.internal</code>, not localhost.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-zinc-400 mb-2">Model</label>
                                <input
                                    type="text"
                                    value={model}
                                    onChange={(event) => {
                                        setModel(event.target.value);
                                        markDirty();
                                    }}
                                    placeholder="auto"
                                    className="input-field font-mono"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-zinc-400 mb-2">Temperature</label>
                                <input
                                    type="number"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    value={temperature}
                                    onChange={(event) => {
                                        setTemperature(event.target.value);
                                        markDirty();
                                    }}
                                    className="input-field"
                                />
                            </div>
                        </div>

                        <details className="rounded-xl border border-white/5 bg-black/10 p-4">
                            <summary className="cursor-pointer text-sm text-zinc-400 hover:text-white">Advanced settings</summary>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                <div>
                                    <label className="block text-xs text-zinc-500 mb-2">Timeout (seconds)</label>
                                    <input
                                        type="number"
                                        min="10"
                                        max="900"
                                        value={timeoutSeconds}
                                        onChange={(event) => {
                                            setTimeoutSeconds(event.target.value);
                                            markDirty();
                                        }}
                                        className="input-field"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-zinc-500 mb-2">Max output tokens</label>
                                    <input
                                        type="number"
                                        min="256"
                                        max="32768"
                                        value={maxTokens}
                                        onChange={(event) => {
                                            setMaxTokens(event.target.value);
                                            markDirty();
                                        }}
                                        className="input-field"
                                    />
                                </div>
                            </div>
                        </details>
                    </>
                )}

                <div>
                    <label className="block text-sm text-zinc-400 mb-2">
                        {isCustom ? 'Router API Key' : 'Gemini API Key'}
                    </label>
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <input
                                type={isVisible ? 'text' : 'password'}
                                value={apiKey}
                                onChange={(event) => {
                                    setApiKey(event.target.value);
                                    markDirty();
                                }}
                                placeholder={isCustom ? 'Router API key' : 'AIzaSy...'}
                                className="input-field pr-12 font-mono"
                            />
                            <button
                                type="button"
                                onClick={() => setIsVisible(!isVisible)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white transition-colors"
                            >
                                {isVisible ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                        <button
                            type="button"
                            onClick={handleSave}
                            disabled={!canSave || isSaved}
                            className={`px-6 rounded-xl font-medium transition-all flex items-center gap-2 ${isSaved
                                ? 'bg-green-500/20 text-green-400 cursor-default'
                                : 'bg-primary hover:bg-blue-600 text-white shadow-lg shadow-primary/20 disabled:opacity-40 disabled:cursor-not-allowed'
                                }`}
                        >
                            {isSaved ? <><Check size={18} /> Ready</> : 'Save AI'}
                        </button>
                    </div>
                </div>
            </div>

            {isCustom ? (
                <div className="mt-4 p-3 rounded-xl border border-amber-500/20 bg-amber-500/5 flex gap-2 text-xs text-amber-200/80 leading-relaxed">
                    <AlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />
                    <span>
                        Custom routing currently covers text-based automatic clip detection. Features that upload video files directly to Gemini still require the Gemini provider.
                    </span>
                </div>
            ) : (
                <p className="mt-3 text-xs text-zinc-500">
                    Your key is stored locally in your browser for convenience.
                    <br />
                    <a
                        href="https://aistudio.google.com/app/apikey"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline mt-1 inline-block"
                    >
                        Get your free Gemini API Key here →
                    </a>
                </p>
            )}
        </div>
    );
}
