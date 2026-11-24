"""AI crawler registry. Role decides the advice:
- search:   indexes pages so AI search can cite you  -> should be ALLOWED to appear in AI answers
- user:     fetches a page live when a user asks       -> should be ALLOWED
- training: collects data to train models              -> a business choice (allowing does not get you cited)
Probe UAs imitate each bot's published user-agent; servers that verify bot IPs may treat them differently."""

_WK = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; {}; {})"

BOTS = [
    # name, company, role, engine shown to user, UA, probe live?
    {"name": "OAI-SearchBot", "company": "OpenAI", "role": "search", "engine": "ChatGPT search",
     "ua": _WK.format("OAI-SearchBot/1.0", "+https://openai.com/searchbot"), "probe": True},
    {"name": "ChatGPT-User", "company": "OpenAI", "role": "user", "engine": "ChatGPT (live browsing)",
     "ua": _WK.format("ChatGPT-User/1.0", "+https://openai.com/bot"), "probe": True},
    {"name": "GPTBot", "company": "OpenAI", "role": "training", "engine": "OpenAI model training",
     "ua": _WK.format("GPTBot/1.1", "+https://openai.com/gptbot"), "probe": True},
    {"name": "Claude-SearchBot", "company": "Anthropic", "role": "search", "engine": "Claude search",
     "ua": _WK.format("Claude-SearchBot/1.0", "+https://www.anthropic.com"), "probe": True},
    {"name": "Claude-User", "company": "Anthropic", "role": "user", "engine": "Claude (live browsing)",
     "ua": _WK.format("Claude-User/1.0", "+https://www.anthropic.com"), "probe": False},
    {"name": "ClaudeBot", "company": "Anthropic", "role": "training", "engine": "Anthropic model training",
     "ua": _WK.format("ClaudeBot/1.0", "+claudebot@anthropic.com"), "probe": True},
    {"name": "PerplexityBot", "company": "Perplexity", "role": "search", "engine": "Perplexity answers",
     "ua": _WK.format("PerplexityBot/1.0", "+https://perplexity.ai/perplexitybot"), "probe": True},
    {"name": "Perplexity-User", "company": "Perplexity", "role": "user", "engine": "Perplexity (live browsing)",
     "ua": _WK.format("Perplexity-User/1.0", "+https://perplexity.ai/perplexity-user"), "probe": False},
    {"name": "Googlebot", "company": "Google", "role": "search", "engine": "Google Search + AI Overviews",
     "ua": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "probe": True},
    {"name": "Google-Extended", "company": "Google", "role": "training", "engine": "Gemini training (robots token)",
     "ua": "", "probe": False},
    {"name": "bingbot", "company": "Microsoft", "role": "search", "engine": "Bing + Copilot",
     "ua": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)", "probe": True},
    {"name": "Applebot-Extended", "company": "Apple", "role": "training", "engine": "Apple Intelligence training (robots token)",
     "ua": "", "probe": False},
    {"name": "meta-externalagent", "company": "Meta", "role": "training", "engine": "Meta AI",
     "ua": "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)", "probe": False},
    {"name": "CCBot", "company": "Common Crawl", "role": "training", "engine": "Open dataset used by many models",
     "ua": "CCBot/2.0 (https://commoncrawl.org/faq/)", "probe": False},
]

ROLE_LABEL = {"search": "AI search", "user": "Live fetch", "training": "Training"}
