import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
    AlertTriangle,
    Check,
    Eye,
    EyeOff,
    Key,
    RefreshCw,
    Server,
    Wifi,
    WifiOff,
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

const normalizeBaseUrl = (value) => value.trim().replace(/\/+$/, '');

const buildModelsUrl = (value) => {
    let base = normalizeBaseUrl(value);
    if (!base) return '';
    base = base.replace(/\/chat\/completions$/i, '');
    if (/\/models$/i.test(base)) return base;
    return `${base}/models`;
};

const extractModelIds = (payload) => {
    const candidates = [];

    if (Array.isArray(payload?.data)) candidates.push(...payload.data);
    if (Array.isArray(payload?.models)) candidates.push(...payload.models);
    if (Array.isArray(payload?.result?.data)) candidates.push(...payload.result.data);
    if (Array.isArray(payload?.result?.models)) candidates.push(...payload.result.models);
    if (Array.isArray(payload)) candidates.push(...payload);

    const ids = candidates
        .map((item) => {
            if (typeof item === 'string') return item;
            if (!item || typeof item !== 'object') return '';
            return item.id || item.name || item.model || item.slug || '';
        })
        .map((value) => String(value).trim())
        .filter(Boolean);

    return [...new Set(ids)].sort((left, right) => {
        const leftGemini = /gemini/i.test(left);
        const rightGemini = /gemini/i.test(right);
        if (leftGemini !== rightGemini) return leftGemini ? -1 : 1;
        return left.localeCompare(right);
    });
};

const defaults = {
    provider: 'openai_compatible',
    apiKey: '',
    baseUrl: '',
    model: '',
    temperature: '0.2',
    timeoutSeconds: '180',
    maxTokens: '4096',
};

const parseSavedValue = (savedKey) => {
    if (!savedKey) return { ...defaults };

    if (!savedKey.startsWith(CONFIG_PREFIX)) {
        return {
            ...defaults,
            provider: 'gemini',
            apiKey: savedKey,
            model: 'gemini-2.5-flash',
        };
    }

    try {
        const raw = decodeUtf8Base64(savedKey.slice(CONFIG_PREFIX.length));
        const parsed = JSON.parse(raw);
        const provider = parsed.provider || 'openai_compatible';

        // Gemini CLI OAuth is no longer offered. Migrate old browser settings to
        // a blank custom endpoint form rather than keeping a dead provider selected.
        if (['gemini_cli_oauth', 'gemini-cli-oauth', 'gemini_cli', 'gemini-cli'].includes(provider)) {
            return { ...defaults };
        }

        return {
            provider,
            apiKey: parsed.apiKey || '',
            baseUrl: parsed.baseUrl || '',
            model: parsed.model || (provider === 'gemini' ? 'gemini-2.5-flash' : ''),
            temperature: String(parsed.temperature ?? 0.2),
            timeoutSeconds: String(parsed.timeoutSeconds ?? 180),
            maxTokens: String(parsed.maxTokens ?? 4096),
        };
    } catch (error) {
        console.warn('Could not read saved AI settings. Resetting the form.');
        return { ...defaults };
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
    const [modelOptions, setModelOptions] = useState([]);
    const [modelStatus, setModelStatus] = useState('idle');
    const [modelError, setModelError] = useState('');
    const [showAllModels, setShowAllModels] = useState(false);
    const fetchSequence = useRef(0);

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
    const requiresApiKey = true;
    const canSave = (
        apiKey.trim().length > 0
        && (!isCustom || (
            baseUrl.trim().length > 0
            && model.trim().length > 0
        ))
    );

    const geminiModels = useMemo(
        () => modelOptions.filter((item) => /gemini/i.test(item)),
        [modelOptions],
    );

    const visibleModels = useMemo(() => {
        if (showAllModels || geminiModels.length === 0) return modelOptions;
        return geminiModels;
    }, [geminiModels, modelOptions, showAllModels]);

    const markDirty = () => setIsSaved(false);

    const fetchModels = useCallback(async ({ silent = false } = {}) => {
        const cleanBaseUrl = normalizeBaseUrl(baseUrl);
        const cleanApiKey = apiKey.trim();
        const modelsUrl = buildModelsUrl(cleanBaseUrl);

        if (!isCustom || !modelsUrl || cleanApiKey.length < 4) {
            setModelOptions([]);
            setModelStatus('idle');
            setModelError('');
            return;
        }

        let parsedUrl;
        try {
            parsedUrl = new URL(modelsUrl);
        } catch (error) {
            setModelOptions([]);
            setModelStatus('error');
            setModelError('Enter a valid HTTP or HTTPS endpoint URL.');
            return;
        }

        if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
            setModelOptions([]);
            setModelStatus('error');
            setModelError('Model discovery only supports HTTP or HTTPS endpoints.');
            return;
        }

        const sequence = fetchSequence.current + 1;
        fetchSequence.current = sequence;
        setModelStatus('loading');
        if (!silent) setModelError('');

        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 20000);

        try {
            const response = await fetch(modelsUrl, {
                method: 'GET',
                headers: {
                    Accept: 'application/json',
                    Authorization: `Bearer ${cleanApiKey}`,
                },
                signal: controller.signal,
            });

            if (!response.ok) {
                const raw = await response.text();
                const safeMessage = raw
                    .replaceAll(cleanApiKey, '***')
                    .replace(/\s+/g, ' ')
                    .trim()
                    .slice(0, 240);
                throw new Error(`HTTP ${response.status}${safeMessage ? `: ${safeMessage}` : ''}`);
            }

            const payload = await response.json();
            const ids = extractModelIds(payload);
            if (ids.length === 0) {
                throw new Error('The endpoint returned no recognizable model IDs.');
            }

            if (fetchSequence.current !== sequence) return;

            const preferred = ids.filter((item) => /gemini/i.test(item));
            setModelOptions(ids);
            setModelStatus('success');
            setModelError('');

            setModel((current) => {
                if (ids.includes(current)) return current;
                return preferred[0] || ids[0];
            });
            setIsSaved(false);
        } catch (error) {
            if (fetchSequence.current !== sequence) return;
            setModelOptions([]);
            setModelStatus('error');
            setModelError(
                error?.name === 'AbortError'
                    ? 'Model discovery timed out after 20 seconds.'
                    : `${error?.message || 'Could not fetch models.'} Check the endpoint, API key, and CORS policy.`,
            );
        } finally {
            window.clearTimeout(timeout);
        }
    }, [apiKey, baseUrl, isCustom]);

    useEffect(() => {
        if (!isCustom || !baseUrl.trim() || apiKey.trim().length < 4) {
            setModelOptions([]);
            setModelStatus('idle');
            setModelError('');
            return undefined;
        }

        const timer = window.setTimeout(() => {
            fetchModels({ silent: true });
        }, 700);

        return () => window.clearTimeout(timer);
    }, [apiKey, baseUrl, fetchModels, isCustom]);

    const handleProviderChange = (event) => {
        const nextProvider = event.target.value;
        setProvider(nextProvider);
        setModelOptions([]);
        setModelError('');
        setModelStatus('idle');

        if (nextProvider === 'gemini') {
            setModel('gemini-2.5-flash');
        } else if (provider === 'gemini') {
            setModel('');
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
            baseUrl: normalizeBaseUrl(baseUrl),
            apiKey: apiKey.trim(),
            model: model.trim(),
            temperature: Number(temperature) || 0.2,
            timeoutSeconds: Number(timeoutSeconds) || 180,
            maxTokens: Number(maxTokens) || 4096,
        };

        onKeySet(CONFIG_PREFIX + encodeUtf8Base64(JSON.stringify(config)));
        setIsSaved(true);
    };

    const icon = isCustom ? <Server size={20} /> : <Key size={20} />;
    const modelsUrl = buildModelsUrl(baseUrl);

    return (
        <div className="bg-surface border border-white/5 rounded-2xl p-6 mb-8 animate-[fadeIn_0.5s_ease-out]">
            <div className="flex items-center gap-3 mb-5">
                <div className="p-2 bg-accent/20 rounded-lg text-accent">{icon}</div>
                <div>
                    <h2 className="text-lg font-semibold">AI Provider</h2>
                    <p className="text-xs text-zinc-500">
                        Custom endpoint model discovery and transcript-based clipping analysis.
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
                        <option value="openai_compatible">
                            Custom Endpoint + API Key
                        </option>
                        <option value="gemini">
                            Google Gemini API Key (direct fallback)
                        </option>
                    </select>
                </div>

                {isCustom && (
                    <>
                        <div>
                            <label className="block text-sm text-zinc-400 mb-2">Base URL</label>
                            <input
                                type="url"
                                value={baseUrl}
                                onChange={(event) => {
                                    setBaseUrl(event.target.value);
                                    markDirty();
                                }}
                                placeholder="https://router.example.com/v1"
                                className="input-field font-mono"
                                autoComplete="url"
                            />
                            <p className="mt-2 text-xs text-zinc-500">
                                OpenShorts automatically requests <code>{modelsUrl || 'BASE_URL/models'}</code> and uses the selected model for chat completions.
                            </p>
                        </div>

                        <ApiKeyInput
                            label="Endpoint API Key"
                            value={apiKey}
                            setValue={setApiKey}
                            isVisible={isVisible}
                            setIsVisible={setIsVisible}
                            dirty={markDirty}
                            placeholder="Endpoint API key"
                        />

                        <div className="rounded-xl border border-white/10 bg-black/10 p-4 space-y-3">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                                <div>
                                    <div className="flex items-center gap-2 text-sm font-medium text-zinc-200">
                                        {modelStatus === 'success'
                                            ? <Wifi size={16} className="text-emerald-400" />
                                            : modelStatus === 'error'
                                                ? <WifiOff size={16} className="text-rose-400" />
                                                : <Server size={16} className="text-zinc-400" />}
                                        Endpoint Models
                                    </div>
                                    <p className="text-xs text-zinc-500 mt-1">
                                        Models are fetched automatically after the URL and API key are entered.
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => fetchModels()}
                                    disabled={!baseUrl.trim() || apiKey.trim().length < 4 || modelStatus === 'loading'}
                                    className="px-3 py-2 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-xs text-zinc-200 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    <RefreshCw size={14} className={modelStatus === 'loading' ? 'animate-spin' : ''} />
                                    {modelStatus === 'loading' ? 'Fetching...' : 'Refresh Models'}
                                </button>
                            </div>

                            {modelStatus === 'success' && (
                                <div className="text-xs text-emerald-300">
                                    Found {modelOptions.length} model{modelOptions.length === 1 ? '' : 's'}, including {geminiModels.length} Gemini model{geminiModels.length === 1 ? '' : 's'}.
                                </div>
                            )}

                            {modelError && (
                                <div className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-3 text-xs text-rose-200">
                                    {modelError}
                                </div>
                            )}

                            {visibleModels.length > 0 ? (
                                <div>
                                    <label className="block text-sm text-zinc-400 mb-2">Gemini Model</label>
                                    <select
                                        value={model}
                                        onChange={(event) => {
                                            setModel(event.target.value);
                                            markDirty();
                                        }}
                                        className="input-field font-mono"
                                    >
                                        {visibleModels.map((item) => (
                                            <option key={item} value={item}>{item}</option>
                                        ))}
                                    </select>

                                    {geminiModels.length > 0 && modelOptions.length > geminiModels.length && (
                                        <label className="mt-3 flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={showAllModels}
                                                onChange={(event) => setShowAllModels(event.target.checked)}
                                                className="rounded border-white/20 bg-black/20"
                                            />
                                            Show all {modelOptions.length} endpoint models
                                        </label>
                                    )}
                                </div>
                            ) : (
                                <Field
                                    label="Model ID (manual fallback)"
                                    value={model}
                                    setValue={setModel}
                                    dirty={markDirty}
                                    placeholder="google/gemini-2.5-flash"
                                />
                            )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <Field label="Temperature" value={temperature} setValue={setTemperature} dirty={markDirty} type="number" />
                            <Field label="Timeout (seconds)" value={timeoutSeconds} setValue={setTimeoutSeconds} dirty={markDirty} type="number" />
                            <Field label="Max output tokens" value={maxTokens} setValue={setMaxTokens} dirty={markDirty} type="number" />
                        </div>
                    </>
                )}

                {!isCustom && (
                    <ApiKeyInput
                        label="Gemini API Key"
                        value={apiKey}
                        setValue={setApiKey}
                        isVisible={isVisible}
                        setIsVisible={setIsVisible}
                        dirty={markDirty}
                        placeholder="AIzaSy..."
                    />
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
                        {isSaved ? <><Check size={18} /> Ready</> : isCustom ? 'Save Endpoint' : 'Save Gemini Key'}
                    </button>
                </div>
            </div>

            {isCustom && (
                <div className="mt-4 p-3 rounded-xl border border-amber-500/20 bg-amber-500/5 flex gap-2 text-xs text-amber-200/80">
                    <AlertTriangle size={16} className="text-amber-400 shrink-0" />
                    <span>
                        Custom endpoints cover text-based clipping analysis. Direct Gemini Files API video uploads still require the direct Gemini API provider.
                    </span>
                </div>
            )}
        </div>
    );
}

function ApiKeyInput({ label, value, setValue, isVisible, setIsVisible, dirty, placeholder }) {
    return (
        <div>
            <label className="block text-sm text-zinc-400 mb-2">{label}</label>
            <div className="relative">
                <input
                    type={isVisible ? 'text' : 'password'}
                    value={value}
                    onChange={(event) => {
                        setValue(event.target.value);
                        dirty();
                    }}
                    placeholder={placeholder}
                    className="input-field pr-12 font-mono"
                    autoComplete="off"
                />
                <button
                    type="button"
                    aria-label={isVisible ? 'Hide API key' : 'Show API key'}
                    onClick={() => setIsVisible(!isVisible)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
                >
                    {isVisible ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
            </div>
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
