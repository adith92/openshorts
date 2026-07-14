import React, { useEffect, useMemo, useState } from 'react';
import {
    AlertTriangle,
    Check,
    Eye,
    EyeOff,
    Key,
    Server,
    Terminal,
} from 'lucide-react';

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

const defaults = {
    provider: 'gemini',
    apiKey: '',
    baseUrl: '',
    model: 'gemini-2.5-flash',
    temperature: '0.2',
    timeoutSeconds: '180',
    maxTokens: '4096',
};

const parseSavedValue = (savedKey) => {
    if (!savedKey || !savedKey.startsWith(CONFIG_PREFIX)) {
        return { ...defaults, apiKey: savedKey || '' };
    }

    try {
        const raw = decodeUtf8Base64(savedKey.slice(CONFIG_PREFIX.length));
        const parsed = JSON.parse(raw);
        const provider = parsed.provider || 'openai_compatible';
        return {
            provider,
            apiKey: parsed.apiKey || '',
            baseUrl: parsed.baseUrl || '',
            model: parsed.model || (provider === 'gemini' ? 'gemini-2.5-flash' : 'auto'),
            temperature: String(parsed.temperature ?? 0.2),
            timeoutSeconds: String(parsed.timeoutSeconds ?? 180),
            maxTokens: String(parsed.maxTokens ?? 4096),
        };
    } catch (error) {
        console.warn('Could not read saved AI settings. Resetting the form.');
        return { ...defaults, provider: 'openai_compatible', model: 'auto' };
    }
};

export default function AIProviderSettings({ onKeySet, savedKey }) {
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
    const isGeminiCli = provider === 'gemini_cli_oauth';
    const requiresApiKey = !isGeminiCli;
    const canSave = (
        (!requiresApiKey || apiKey.trim().length > 0)
        && (!isCustom || (baseUrl.trim().length > 0 && model.trim().length > 0))
    );

    const markDirty = () => setIsSaved(false);

    const handleProviderChange = (event) => {
        const nextProvider = event.target.value;
        setProvider(nextProvider);

        if (nextProvider === 'gemini' && ['', 'auto', 'default'].includes(model)) {
            setModel('gemini-2.5-flash');
        }
        if (
            ['openai_compatible', 'gemini_cli_oauth'].includes(nextProvider)
            && model === 'gemini-2.5-flash'
        ) {
            setModel('auto');
        }
        markDirty();
    };

    const handleSave = () => {
        if (!canSave) return;

        if (provider === 'gemini') {
            onKeySet(apiKey.trim());
            setIsSaved(true);
            return;
        }

        const config = {
            provider,
            model: model.trim() || 'auto',
            timeoutSeconds: Number(timeoutSeconds) || 180,
        };

        if (isCustom) {
            config.baseUrl = baseUrl.trim().replace(/\/+$/, '');
            config.apiKey = apiKey.trim();
            config.temperature = Number(temperature) || 0.2;
            config.maxTokens = Number(maxTokens) || 4096;
        }

        onKeySet(CONFIG_PREFIX + encodeUtf8Base64(JSON.stringify(config)));
        setIsSaved(true);
    };

    const icon = isGeminiCli
        ? <Terminal size={20} />
        : isCustom
            ? <Server size={20} />
            : <Key size={20} />;

    return (
        <div className="bg-surface border border-white/5 rounded-2xl p-6 mb-8 animate-[fadeIn_0.5s_ease-out]">
            <div className="flex items-center gap-3 mb-5">
                <div className="p-2 bg-accent/20 rounded-lg text-accent">{icon}</div>
                <div>
                    <h2 className="text-lg font-semibold">AI Provider</h2>
                    <p className="text-xs text-zinc-500">
                        Used for transcript-based automatic viral clip detection.
                    </p>
                </div>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm text-zinc-400 mb-2">Provider</label>
                    <select
                        value={provider}
                        onChange={handleProviderChange}
                        className="input-field"
                    >
                        <option value="gemini">Google Gemini API Key</option>
                        <option value="openai_compatible">
                            OpenAI Compatible / Custom Endpoint
                        </option>
                        <option value="gemini_cli_oauth">
                            Gemini CLI OAuth / Sign in with Google
                        </option>
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
                                Use the Docker service name or <code>host.docker.internal</code>, not localhost.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Field label="Model" value={model} setValue={setModel} dirty={markDirty} placeholder="auto" />
                            <Field label="Temperature" value={temperature} setValue={setTemperature} dirty={markDirty} type="number" />
                            <Field label="Timeout (seconds)" value={timeoutSeconds} setValue={setTimeoutSeconds} dirty={markDirty} type="number" />
                            <Field label="Max output tokens" value={maxTokens} setValue={setMaxTokens} dirty={markDirty} type="number" />
                        </div>
                    </>
                )}

                {isGeminiCli && (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Field label="Gemini CLI Model" value={model} setValue={setModel} dirty={markDirty} placeholder="auto" />
                            <Field label="Timeout (seconds)" value={timeoutSeconds} setValue={setTimeoutSeconds} dirty={markDirty} type="number" />
                        </div>

                        <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4 text-xs leading-relaxed">
                            <p className="font-semibold text-blue-300 mb-2">One-time OAuth login inside Docker</p>
                            <code className="block overflow-x-auto rounded-lg bg-black/30 p-3 text-zinc-300">
                                docker compose exec backend sh -lc 'NO_BROWSER=true gemini'
                            </code>
                            <p className="mt-3 text-zinc-400">
                                Follow the URL/code shown in the terminal. Credentials are stored in the persistent <code>gemini-cli-data</code> Docker volume.
                            </p>
                        </div>
                    </>
                )}

                {requiresApiKey && (
                    <div>
                        <label className="block text-sm text-zinc-400 mb-2">
                            {isCustom ? 'Router API Key' : 'Gemini API Key'}
                        </label>
                        <div className="relative">
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
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
                            >
                                {isVisible ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>
                )}

                <div className="flex justify-end">
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={!canSave || isSaved}
                        className={`px-6 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all ${
                            isSaved
                                ? 'bg-green-500/20 text-green-400 cursor-default'
                                : 'bg-primary hover:bg-blue-600 text-white disabled:opacity-40 disabled:cursor-not-allowed'
                        }`}
                    >
                        {isSaved ? <><Check size={18} /> Ready</> : 'Save AI'}
                    </button>
                </div>
            </div>

            {(isCustom || isGeminiCli) && (
                <div className="mt-4 p-3 rounded-xl border border-amber-500/20 bg-amber-500/5 flex gap-2 text-xs text-amber-200/80">
                    <AlertTriangle size={16} className="text-amber-400 shrink-0" />
                    <span>
                        This provider covers text-based clipping analysis. Direct Gemini Files API video uploads still require the Gemini API provider.
                    </span>
                </div>
            )}
        </div>
    );
}

function Field({ label, value, setValue, dirty, type = 'text', placeholder = '' }) {
    return (
        <div>
            <label className="block text-sm text-zinc-400 mb-2">{label}</label>
            <input
                type={type}
                value={value}
                placeholder={placeholder}
                onChange={(event) => {
                    setValue(event.target.value);
                    dirty();
                }}
                className="input-field font-mono"
            />
        </div>
    );
}
