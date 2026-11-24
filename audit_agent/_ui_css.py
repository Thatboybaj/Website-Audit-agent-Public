CSS = r"""
/* AuditPilot — part of the Pilot agents family (LeadPilot, ProspectPilot): light dashboard, sidebar shell,
   hairline cards, family blue. Its own identity: violet AI-search accent, Instrument Sans + Geist Mono,
   scan mark, dial gauges, blueprint dot-grid. */
:root{--bg:#f4f5f7;--panel:#fff;--panel-2:#fafbfc;--side:#fbfbfc;--hover:#f1f2f5;--ink:#12141a;--ink-2:#353a45;--muted:#667085;--faint:#98a1b0;
--line:#e6e8ee;--line-2:#d7dbe3;--brand:#2b4ad8;--brand-ink:#1f37a8;--brand-soft:#edf0fd;--aeo:#6f47e8;--aeo-ink:#5532c9;--aeo-soft:#f1ecfe;
--good:#14804a;--warn:#b26a00;--bad:#d03535;--good-bg:#e8f6ee;--warn-bg:#fdf3e1;--bad-bg:#fdeceb;
--lock:#b9bfcc;--track:#eceef3;--dotc:#d9dde6;--r:14px;--rs:9px;--shadow:0 1px 2px rgba(16,24,40,.04);--shadow-2:0 1px 2px rgba(16,24,40,.05),0 16px 40px -24px rgba(16,24,40,.35);
--fb:"Instrument Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--fm:"Geist Mono",ui-monospace,"SF Mono",Menlo,monospace;color-scheme:light}
@media(prefers-color-scheme:dark){:root{--bg:#121318;--panel:#17181e;--panel-2:#1b1c23;--side:#15161b;--hover:#21232b;--ink:#ecedf1;--ink-2:#c9ccd5;--muted:#9a9fac;--faint:#6d7280;
--line:#272932;--line-2:#323542;--brand:#6f8bff;--brand-ink:#9db0ff;--brand-soft:#1c2340;--aeo:#a58bff;--aeo-ink:#c3b2ff;--aeo-soft:#251d40;
--good:#4cc38a;--warn:#f0b45a;--bad:#ff7b72;--good-bg:#13291e;--warn-bg:#2d2312;--bad-bg:#2f1715;--lock:#454a58;--track:#262833;--dotc:#2a2d38;
--shadow:0 1px 0 rgba(255,255,255,.02);--shadow-2:0 1px 2px rgba(0,0,0,.4),0 16px 40px -24px rgba(0,0,0,.7);color-scheme:dark}}
*{box-sizing:border-box}[hidden]{display:none!important}html{overflow-x:clip}
body{margin:0;background:var(--bg);color:var(--ink);font:400 14px/1.55 var(--fb);-webkit-font-smoothing:antialiased}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:6px}
h1,h2,h3,h4{margin:0;letter-spacing:-.02em;font-weight:600}h3{font-size:17px}
.mono,.mlabel,.tag,.chip,.n{font-family:var(--fm)}
.mlabel{font-size:10.5px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
.dim{color:var(--muted)}.okc{color:var(--good)}.bad{color:var(--bad)}.mid{color:var(--warn)}
/* ---------- shell */
.app{display:grid;grid-template-columns:244px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;display:flex;flex-direction:column;background:var(--side);border-right:1px solid var(--line);padding:18px 14px;overflow:auto}
.logo{display:flex;align-items:center;gap:10px;padding:4px 8px 18px;color:var(--ink);text-decoration:none!important;cursor:pointer;border:0;background:none;text-align:left}
.mark{width:30px;height:30px;flex:none;display:block}
.bname{font-weight:600;font-size:14.5px;letter-spacing:-.01em;line-height:1.2}.bsub{display:block;font:500 10px var(--fm);letter-spacing:.06em;text-transform:uppercase;color:var(--faint)}
.navl{font:500 10px var(--fm);letter-spacing:.1em;text-transform:uppercase;color:var(--faint);padding:14px 10px 6px}
.nav{display:flex;align-items:center;gap:10px;width:100%;padding:8px 10px;border-radius:9px;border:0;background:none;color:var(--ink-2);font-weight:500;font-size:13.5px;cursor:pointer;text-align:left;margin-bottom:2px}
.nav svg{width:16px;height:16px;opacity:.65;flex:none}.nav:hover{background:var(--hover);color:var(--ink)}
.nav.on{background:var(--brand-soft);color:var(--brand-ink);font-weight:600}.nav.on svg{opacity:1}.nav:disabled{opacity:.4;cursor:default;background:none}
.nav .cnt{margin-left:auto;font:500 11px var(--fm);color:var(--faint)}
.sfoot{margin-top:auto;padding-top:14px}
.plancard{border:1px solid var(--line);border-radius:12px;padding:12px;background:var(--panel)}
.plan{display:inline-flex;align-items:center;gap:7px;border:0;background:none;padding:0;font:500 11px var(--fm);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);cursor:pointer}
.pdot{width:7px;height:7px;border-radius:50%;background:var(--faint)}.plan.pro .pdot{background:var(--aeo)}.plan.owner .pdot{background:var(--good)}
.plancard p{margin:6px 0 10px;font-size:12px;color:var(--muted);line-height:1.45}.plancard .btn{width:100%}
.made{font-size:11px;color:var(--faint);padding:12px 6px 0}
.main{min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:14px;padding:12px 32px;background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.crumb{font-size:12px;color:var(--faint)}.topbar h1{font-size:15px}
.status{margin-left:auto;display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.status span{display:inline-flex;align-items:center;gap:6px}.status i{width:6px;height:6px;border-radius:50%;background:var(--lock)}.status i.on{background:var(--good);box-shadow:0 0 0 3px var(--good-bg)}
.btn.mtoggle{display:none}
.content{padding:26px 32px 64px;max-width:1280px;width:100%}
.view{display:none;animation:fade .3s ease}.view.on{display:block}@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.phead{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}
.phead h2{font-size:24px;letter-spacing:-.03em}.phead p{margin:4px 0 0;color:var(--muted);max-width:66ch}
/* ---------- primitives */
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;height:36px;padding:0 14px;border-radius:var(--rs);border:1px solid var(--line-2);background:var(--panel);color:var(--ink);font-weight:550;font-size:13px;cursor:pointer;white-space:nowrap;transition:background .12s,border-color .12s,transform .08s;text-decoration:none!important}
.btn:hover{background:var(--hover)}.btn:active{transform:translateY(1px)}.btn:disabled{opacity:.55;cursor:wait;transform:none}
.btn.light{background:var(--brand);border-color:var(--brand);color:#fff}.btn.light:hover{background:var(--brand-ink);border-color:var(--brand-ink)}
.btn.blue{background:linear-gradient(135deg,var(--brand),var(--aeo));border-color:transparent;color:#fff}.btn.blue:hover{filter:brightness(1.08)}
.btn.ghost{background:var(--panel)}.btn.sm{height:30px;padding:0 11px;font-size:12.5px;border-radius:8px}.btn.icon{width:34px;padding:0}
.tag{display:inline-flex;align-items:center;gap:4px;font-size:10.5px;letter-spacing:.04em;text-transform:uppercase;padding:2px 7px;border-radius:6px;background:var(--hover);color:var(--muted);white-space:nowrap}
.tag.ok{background:var(--good-bg);color:var(--good)}.tag.warn{background:var(--warn-bg);color:var(--warn)}.tag.fail{background:var(--bad-bg);color:var(--bad)}.tag.blue{background:var(--aeo-soft);color:var(--aeo-ink)}
.chips{display:flex;gap:6px;flex-wrap:wrap}.chip{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:4px 10px;background:var(--panel)}
.chip i{width:6px;height:6px;border-radius:50%;background:var(--faint)}.chip i.ok{background:var(--brand)}.chip i.blue{background:var(--aeo)}
.err{color:var(--bad);font-size:13px;margin-top:10px;min-height:18px}
.empty{padding:40px;text-align:center;color:var(--muted)}
/* ---------- new audit */
.runner{position:relative;overflow:hidden;padding:26px 26px 18px;margin-bottom:14px}
.runner:before{content:"";position:absolute;inset:0;background-image:radial-gradient(var(--dotc) 1px,transparent 1px);background-size:16px 16px;-webkit-mask-image:linear-gradient(100deg,transparent 35%,#000 95%);mask-image:linear-gradient(100deg,transparent 35%,#000 95%);pointer-events:none}
.runner>*{position:relative}.runner h3{font-size:20px;letter-spacing:-.03em;margin:6px 0 4px}.runner>p{margin:0 0 18px;color:var(--muted);max-width:60ch}
.bar{display:flex;align-items:center;gap:8px;background:var(--panel);border:1px solid var(--line-2);border-radius:12px;padding:6px 6px 6px 14px;max-width:720px;box-shadow:var(--shadow-2);transition:border-color .15s,box-shadow .15s}
.bar:focus-within{border-color:var(--brand);box-shadow:0 0 0 4px var(--brand-soft)}
.bar-ico{color:var(--faint);font-family:var(--fm)}.bar input{flex:1;min-width:0;border:0;outline:none;background:none;color:var(--ink);font:500 15px var(--fb);padding:9px 4px}
.bar input::placeholder{color:var(--faint)}.runner .chips{margin-top:12px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.pane{padding:18px}.ph{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px}
.alist{list-style:none;margin:0;padding:0;counter-reset:a}.alist li{display:flex;gap:12px;padding:8px 0;border-top:1px solid var(--line);font-size:13.5px;font-weight:500}
.alist li:before{counter-increment:a;content:counter(a,decimal-leading-zero);font:500 11px var(--fm);color:var(--faint);padding-top:2px}.alist small{display:block;color:var(--muted);font-weight:400;font-size:12.5px}
.log{padding:18px;margin-bottom:14px}.logline{display:flex;gap:12px;font:400 12.5px var(--fm);color:var(--muted);padding:7px 0;border-top:1px dashed var(--line);animation:fade .3s ease}
.logline .t{color:var(--faint);width:56px;flex:none}.logline b{font-weight:500;color:var(--brand);width:16px}.logline.done b{color:var(--good)}
.scan{height:3px;border-radius:3px;background:var(--track);overflow:hidden;margin:12px 0 8px}.scan i{display:block;height:100%;width:30%;background:linear-gradient(90deg,var(--brand),var(--aeo));border-radius:3px;animation:scan 1.4s ease-in-out infinite}
@keyframes scan{0%{transform:translateX(-100%)}100%{transform:translateX(340%)}}
/* ---------- results */
.rbar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:16px 20px;flex-wrap:wrap}
.rbar h2{font-size:22px;letter-spacing:-.03em;margin-top:2px;word-break:break-all}.acts{display:flex;gap:8px;flex-wrap:wrap}
.scores{display:grid;grid-template-columns:1.2fr 1.2fr .8fr .8fr;gap:14px;margin-top:14px}
.sc{padding:18px 20px}.gwrap{display:flex;gap:16px;align-items:center;margin-top:8px}
.ring{width:132px;height:84px;flex:none;color:var(--ink)}
.band{display:inline-block;font:500 10.5px var(--fm);letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:6px;margin-bottom:6px}
.sc p{margin:0;color:var(--muted);font-size:13px}.sc.dim{opacity:.7}
.delta{font:500 11px var(--fm);margin-left:6px;text-transform:none;letter-spacing:0}.up{color:var(--good)}.down{color:var(--bad)}
.statn{display:flex;gap:18px;margin-top:12px}.statn b{display:block;font:600 30px/1 var(--fb);letter-spacing:-.03em;font-variant-numeric:tabular-nums}.statn span{font:500 10.5px var(--fm);color:var(--faint);text-transform:uppercase;letter-spacing:.06em}
.tabs{display:flex;gap:2px;margin:20px 0 14px;border-bottom:1px solid var(--line);overflow-x:auto}
.tab{background:none;border:0;padding:10px 14px;font-weight:500;font-size:13.5px;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;display:inline-flex;align-items:center;gap:6px;margin-bottom:-1px}
.tab:hover{color:var(--ink)}.tab.on{color:var(--ink);border-color:var(--brand)}
.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}.grid.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.area{padding:16px;cursor:pointer;text-align:left;width:100%;transition:border-color .15s,box-shadow .15s,transform .15s}
.area:hover{border-color:var(--line-2);box-shadow:var(--shadow-2);transform:translateY(-1px)}
.area h4{margin:8px 0 2px;font-size:14.5px}.area .s{font:600 34px/1 var(--fb);letter-spacing:-.04em;margin:10px 0 8px;font-variant-numeric:tabular-nums}.area .s small{font-size:12px;color:var(--faint);font-weight:500;letter-spacing:0}
.bar2{height:4px;border-radius:4px;background:var(--track);overflow:hidden}.bar2 i{display:block;height:100%;border-radius:4px}
.dots{display:flex;gap:3px;margin-top:10px;flex-wrap:wrap}.dots i{width:8px;height:8px;border-radius:2px}
.p{background:var(--good)}.w{background:var(--warn)}.f{background:var(--bad)}.s0{background:var(--track)}.l{background:var(--lock)}
.km{display:flex;justify-content:space-between;gap:8px;margin-top:10px;font-size:12px;color:var(--muted)}.km b{color:var(--ink);font-weight:600}
.panel2{padding:18px}.split{display:grid;grid-template-columns:1.45fr 1fr;gap:14px;margin-bottom:14px}
.prio{list-style:none;margin:0;padding:0}.prio li{display:grid;grid-template-columns:26px 1fr;gap:8px;padding:12px 0;border-top:1px solid var(--line)}
.prio .n{font-size:11px;color:var(--faint);padding-top:2px}.prio b{font-weight:600}.prio p{margin:3px 0 0;color:var(--muted);font-size:13px}.prio .fx{color:var(--ink)}
.meta{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}
.summary{white-space:pre-wrap;color:var(--ink-2);font-size:14px;margin:8px 0 0}
.serp{background:#fff;color:#202124;border:1px solid var(--line);border-radius:10px;padding:14px 16px;font-family:Arial,sans-serif;margin-top:8px}
.serp .u{font-size:13px;color:#4d5156}.serp .t{font-size:19px;color:#1a0dab;margin:3px 0}.serp .d{font-size:14px;color:#4d5156;line-height:1.5}
.kv{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:14px}.kv div{background:var(--panel-2);border:1px solid var(--line);border-radius:10px;padding:10px 12px;min-width:0}
.kv b{display:block;font-size:17px;margin-top:4px;letter-spacing:-.02em;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;font-size:13px}th{font:500 10.5px var(--fm);letter-spacing:.06em;text-transform:uppercase;color:var(--faint);text-align:left;padding:10px 14px;white-space:nowrap;background:var(--panel-2);border-bottom:1px solid var(--line)}
td{padding:10px 14px;border-top:1px solid var(--line);vertical-align:top}tr:nth-child(2) td{border-top:0}.tablewrap{overflow-x:auto}
tr.row{cursor:pointer}tr.row:hover td{background:var(--hover)}
.pill{display:inline-block;min-width:38px;text-align:center;padding:2px 8px;border-radius:6px;font:600 12px var(--fm);color:#fff}
.st{display:inline-flex;align-items:center;gap:6px;font:500 12px var(--fm)}.st i{width:7px;height:7px;border-radius:50%}
.techg{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.techg .card{padding:16px}.techg .chips{margin-top:10px}.techg .chip{color:var(--ink)}
.code{position:relative;margin-top:10px}.code pre{margin:0;background:#0f1117;border:1px solid #1f2230;border-radius:10px;padding:14px;overflow:auto;max-height:320px;font:12px/1.6 var(--fm);color:#d7dcf5}
.code .cbtn{position:absolute;top:8px;right:8px;display:flex;gap:6px}.code .cbtn .btn{background:#1b1e29;border-color:#2b2f3f;color:#e7e9f3}
.fixc{padding:18px;margin-bottom:12px}.fixc p{color:var(--muted);font-size:13px;margin:4px 0 0}
.todo{list-style:none;margin:0;padding:0}.todo li{display:grid;grid-template-columns:22px 1fr auto;gap:12px;padding:12px 0 12px 14px;border-top:1px solid var(--line);align-items:start;position:relative}
.todo li:before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:3px;border-radius:3px;background:var(--line-2)}
.todo li.sev-fail:before{background:var(--bad)}.todo li.sev-warn:before{background:var(--warn)}
.todo input{width:16px;height:16px;accent-color:var(--brand);margin-top:3px}.todo li.done b,.todo li.done p{text-decoration:line-through;opacity:.45}
.todo p{margin:3px 0 0;color:var(--muted);font-size:13px}
.prog{height:6px;border-radius:6px;background:var(--track);overflow:hidden;margin:10px 0 4px}.prog i{display:block;height:100%;background:var(--brand)}
.lock{position:relative}.lock .blur{filter:blur(4px);opacity:.6;pointer-events:none;user-select:none}
.upsell{padding:22px;border-color:color-mix(in srgb,var(--aeo) 30%,var(--line));background:linear-gradient(120deg,var(--aeo-soft),var(--panel) 65%);display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;margin-bottom:14px}
.upsell h3{font-size:20px;letter-spacing:-.03em;margin:4px 0}.upsell p{margin:0;color:var(--muted);max-width:600px}
.big{font:600 40px/1 var(--fb);letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.sov{font:600 64px/1 var(--fb);letter-spacing:-.05em;color:var(--aeo)}
.vq{padding:12px 0;border-top:1px solid var(--line)}.vq summary{cursor:pointer;display:flex;gap:8px;align-items:center;list-style:none;flex-wrap:wrap}
.vq p{color:var(--muted);font-size:13px;margin:8px 0}.vq .src{font:11.5px var(--fm);color:var(--faint);word-break:break-all}
.comp{display:flex;align-items:center;gap:10px;padding:5px 0;font-size:13px}.comp .bar2{flex:1}
textarea,.inp{width:100%;background:var(--panel);border:1px solid var(--line-2);border-radius:9px;color:var(--ink);font:14px/1.5 var(--fb);padding:9px 12px;outline:none}
textarea:focus,.inp:focus{border-color:var(--brand);box-shadow:0 0 0 3px var(--brand-soft)}
label.fl{display:block;font-size:12px;font-weight:500;color:var(--muted);margin:12px 0 5px}
/* ---------- drawer & modal */
.drawer,.modal{position:fixed;inset:0;z-index:60;background:rgba(10,12,18,.32);backdrop-filter:blur(2px);display:none}
.drawer.on{display:block}.modal.on{display:grid;place-items:center;padding:14px}
.dpanel{position:absolute;right:12px;top:12px;bottom:12px;width:min(560px,calc(100% - 24px));overflow:auto;padding:22px;box-shadow:var(--shadow-2);animation:slide .3s ease}
@keyframes slide{from{transform:translateX(16px);opacity:0}to{transform:none;opacity:1}}
.chk{padding:14px 0;border-top:1px solid var(--line)}.chk h5{margin:0;font-size:14px;font-weight:600;display:flex;gap:10px;align-items:center}
.chk p{margin:5px 0 0;color:var(--muted);font-size:13px}.chk code{display:block;font:11.5px var(--fm);color:var(--faint);margin-top:4px;word-break:break-all}.chk .fx{color:var(--ink)}
.mbox{position:relative;width:min(500px,100%);max-height:calc(100vh - 28px);overflow:auto;padding:24px;box-shadow:var(--shadow-2);animation:fade .3s ease}
.mbox h2{font-size:24px;letter-spacing:-.03em;margin:6px 0 2px}.mbox h3{margin-top:22px}.mtabs{display:flex;gap:6px;margin:14px 0 4px}.mtabs button{flex:1}
.toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%) translateY(16px);background:var(--ink);color:var(--panel);padding:10px 16px;border-radius:10px;font-weight:550;font-size:13px;opacity:0;transition:.3s;z-index:70;pointer-events:none}
.toast.on{opacity:1;transform:translateX(-50%)}
.scrim{display:none}
/* ---------- responsive */
@media(max-width:1180px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.scores{grid-template-columns:1fr 1fr}}
@media(max-width:900px){.app{grid-template-columns:1fr}.side{position:fixed;inset:0 auto 0 0;width:264px;z-index:50;transform:translateX(-100%);transition:transform .25s;box-shadow:var(--shadow-2)}
.side.open{transform:none}.side.open+.scrim{display:block;position:fixed;inset:0;z-index:45;background:rgba(10,12,18,.3)}
.btn.mtoggle{display:inline-flex}.topbar{padding:10px 16px}.content{padding:18px 16px 56px}.status{display:none}
.two,.split,.techg{grid-template-columns:1fr}.kv{grid-template-columns:repeat(2,1fr)}.grid,.grid.g3{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:560px){.bar{flex-wrap:wrap}.bar .btn{width:100%}.scores,.grid,.grid.g3{grid-template-columns:1fr}.runner{padding:20px 16px}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""
