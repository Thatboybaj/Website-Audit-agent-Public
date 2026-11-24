CSS = r"""
:root{--ink:#07080b;--ink-2:#0e1116;--ink-3:#141822;--ledger:#f4f1ea;--blue:#2340d9;--blue-ink:#8ea0ff;--grey:#a9aeb7;--grey-2:#6b7079;
--line:rgba(244,241,234,.08);--line-2:rgba(244,241,234,.14);--pass:#5fd39a;--warn:#f2b84b;--fail:#ff6b6b;--lock:#4b5160;
--r:18px;--wrap:1240px;--ease:cubic-bezier(.16,1,.3,1);--fd:"Funnel Display",sans-serif;--fb:"Inter Tight",system-ui,sans-serif;--fm:"JetBrains Mono",ui-monospace,monospace;color-scheme:dark}
*{box-sizing:border-box}[hidden]{display:none!important}html{scroll-behavior:smooth;overflow-x:clip}
body{margin:0;background:var(--ink);color:var(--ledger);font:400 16px/1.55 var(--fb);-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:var(--blue-ink);text-decoration:none}a:hover{text-decoration:underline}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--blue-ink);outline-offset:3px;border-radius:6px}
.globe{position:fixed;right:-260px;top:-160px;width:1100px;height:1100px;color:rgba(142,160,255,.13);pointer-events:none;z-index:0;animation:spin 140s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.glow{position:fixed;inset:0;pointer-events:none;z-index:0;background:radial-gradient(45% 40% at 85% 5%,rgba(35,64,217,.28),transparent 70%),radial-gradient(30% 30% at 5% 100%,rgba(35,64,217,.10),transparent 70%)}
.wrap{max-width:var(--wrap);margin:0 auto;padding:0 32px;position:relative;z-index:1}
.mono,.mlabel,.eyebrow,.links a,.tag,.chip{font-family:var(--fm)}
.mlabel{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--grey)}
.eyebrow{display:flex;align-items:center;gap:10px;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--grey)}
.dot{width:6px;height:6px;border-radius:50%;background:var(--blue-ink);box-shadow:0 0 0 4px rgba(142,160,255,.15)}
.grad{color:var(--blue-ink);background:linear-gradient(90deg,#8ea0ff,#b9c4ff 60%,#8ea0ff);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.card{background:linear-gradient(180deg,rgba(20,24,34,.82),rgba(14,17,22,.82));border:1px solid var(--line);border-radius:var(--r);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.btn{border:1px solid var(--line-2);background:transparent;border-radius:999px;padding:12px 20px;font-weight:600;cursor:pointer;display:inline-flex;gap:8px;align-items:center;justify-content:center;transition:.25s var(--ease);white-space:nowrap}
.btn:hover{border-color:rgba(244,241,234,.3);transform:translateY(-1px)}
.btn.light{background:var(--ledger);color:#0e1116;border-color:var(--ledger)}.btn.light:hover{background:#fff}
.btn.blue{background:var(--blue);border-color:var(--blue);color:#fff}.btn.blue:hover{background:#2e4cf0}
.btn.ghost{background:rgba(244,241,234,.04)}.btn.sm{padding:8px 14px;font-size:14px}
.btn:disabled{opacity:.5;cursor:wait;transform:none}
.tag{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;padding:4px 9px;border-radius:999px;border:1px solid var(--line-2);color:var(--grey)}
.tag.ok{color:var(--pass);border-color:rgba(95,211,154,.35)}.tag.blue{color:var(--blue-ink);border-color:rgba(142,160,255,.4)}
.tag.warn{color:var(--warn);border-color:rgba(242,184,75,.35)}.tag.fail{color:var(--fail);border-color:rgba(255,107,107,.35)}
/* nav */
.nav{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 32px;max-width:var(--wrap);margin:0 auto}
.nav:before{content:"";position:absolute;top:0;bottom:0;left:calc(50% - 50vw);right:calc(50% - 50vw);background:rgba(7,8,11,.72);backdrop-filter:blur(14px);border-bottom:1px solid var(--line);z-index:-1}
.logo{display:flex;align-items:center;gap:10px;font:500 21px var(--fd);letter-spacing:-.03em;color:var(--ledger)}.logo:hover{text-decoration:none}
.logo.sm{font-size:17px}
.mark{width:22px;height:22px;border-radius:50%;border:2.2px solid var(--blue-ink);position:relative}.mark:after{content:"";position:absolute;inset:5px;border-radius:50%;background:var(--ledger)}
.links{display:flex;gap:28px}.links a{color:var(--grey);font-size:11.5px;letter-spacing:.14em;text-transform:uppercase}.links a:hover{color:var(--ledger);text-decoration:none}
.navr{display:flex;gap:10px;align-items:center}
.plan{display:flex;align-items:center;gap:8px;border:1px solid var(--line-2);background:transparent;border-radius:999px;padding:8px 14px;font:500 12px var(--fm);letter-spacing:.06em;cursor:pointer;color:var(--grey)}
.pdot{width:7px;height:7px;border-radius:50%;background:var(--grey-2)}.plan.pro .pdot{background:var(--blue-ink);box-shadow:0 0 0 3px rgba(142,160,255,.2)}.plan.owner .pdot{background:var(--pass)}
.plan.pro,.plan.owner{color:var(--ledger)}
/* views */
.view{display:none;animation:fade .5s var(--ease)}.view.on{display:block}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
/* hero */
.hero{display:grid;grid-template-columns:1.15fr .85fr;gap:48px;align-items:center;padding-top:72px;padding-bottom:40px;min-height:calc(100vh - 160px)}
h1{font:500 clamp(46px,5.8vw,86px)/.95 var(--fd);letter-spacing:-.055em;margin:22px 0 22px}
h2{font:500 clamp(30px,3.6vw,50px)/1 var(--fd);letter-spacing:-.045em;margin:14px 0 0}
h3{font:500 22px var(--fd);letter-spacing:-.03em;margin:10px 0 6px}
.lede{font-size:19px;color:var(--grey);max-width:560px;margin:0 0 30px}
.bar{display:flex;align-items:center;gap:8px;background:rgba(7,8,11,.7);border:1px solid var(--line-2);border-radius:999px;padding:7px 7px 7px 20px;max-width:620px;transition:.3s var(--ease)}
.bar:focus-within{border-color:rgba(142,160,255,.6);box-shadow:0 0 0 6px rgba(35,64,217,.15)}
.bar-ico{color:var(--blue-ink);font-size:18px}
.bar input{flex:1;min-width:0;background:none;border:0;outline:none;color:var(--ledger);font:500 17px var(--fb);padding:12px 4px}
.bar input::placeholder{color:var(--grey-2)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.chip{display:inline-flex;align-items:center;gap:8px;font-size:11.5px;letter-spacing:.06em;color:var(--grey);border:1px solid var(--line);border-radius:999px;padding:6px 12px}
.chip i{width:6px;height:6px;border-radius:50%;background:var(--grey-2)}.chip i.ok{background:var(--pass)}.chip i.blue{background:var(--blue-ink)}
.err{color:var(--fail);font-size:14px;margin-top:12px;min-height:20px}
/* inspector cards */
.hero-r{position:relative;height:440px}
.insp{position:absolute;padding:18px 20px;width:88%;transition:.6s var(--ease)}
.insp .ih{display:flex;justify-content:space-between;font:500 11px var(--fm);letter-spacing:.1em;text-transform:uppercase;color:var(--grey-2);margin-bottom:8px}
.insp b{display:block;font-weight:500;font-size:16px}.insp small{display:block;color:var(--grey-2);font:400 12px var(--fm);margin-top:6px;letter-spacing:.02em}
.insp .warnc{color:var(--warn)}
.c1{top:0;left:10%;opacity:.55}.c2{top:92px;left:4%;opacity:.8}.c3{top:190px;left:0;width:96%;border-color:rgba(142,160,255,.25);box-shadow:0 30px 80px rgba(0,0,0,.5),0 0 0 1px rgba(35,64,217,.2)}
.vrow{display:flex;gap:40px;margin:6px 0 2px}.big{font:500 58px/1 var(--fd);letter-spacing:-.05em}.big.blue{color:var(--blue-ink)}
.hero-r.running .insp{opacity:1}
.log{position:absolute;inset:0;padding:22px;overflow:hidden}
.logline{display:flex;gap:12px;font:400 13px var(--fm);color:var(--grey);padding:7px 0;border-bottom:1px dashed var(--line);animation:fade .4s var(--ease)}
.logline .t{color:var(--grey-2);width:58px;flex:none}.logline.done b{color:var(--pass);font-weight:400}.logline b{color:var(--blue-ink);font-weight:400;width:18px}
.marquee{display:flex;gap:28px;align-items:center;flex-wrap:wrap;color:var(--grey-2);font-size:14px;padding-bottom:30px}.marquee span{font:500 11px var(--fm);letter-spacing:.14em;text-transform:uppercase}
.marquee b{font:500 20px var(--fd);letter-spacing:-.02em;color:rgba(244,241,234,.55)}
/* sections */
.sec{padding:90px 32px 10px}.sec-h{margin-bottom:34px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.three{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.pane{padding:26px}.ph{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.blue-edge{border-color:rgba(142,160,255,.28);background:linear-gradient(180deg,rgba(35,64,217,.14),rgba(14,17,22,.85))}
.alist{list-style:none;margin:0;padding:0;counter-reset:a}.alist li{display:flex;gap:14px;padding:11px 0;border-top:1px solid var(--line);font-size:15px}
.alist li:before{counter-increment:a;content:counter(a,decimal-leading-zero);font:500 11px var(--fm);color:var(--grey-2);padding-top:4px}
.alist small{display:block;color:var(--grey-2);font-size:13px}
.step{padding:26px}.step p{color:var(--grey);margin:0;font-size:15px}
.price{padding:30px;display:flex;flex-direction:column}.price .amt{font:500 52px/1 var(--fd);letter-spacing:-.05em;margin:14px 0 4px}.price .amt small{font-size:16px;color:var(--grey);letter-spacing:0}
.price ul{list-style:none;padding:0;margin:20px 0 26px;flex:1}.price li{padding:8px 0;border-top:1px solid var(--line);font-size:15px;display:flex;gap:10px}
.price li:before{content:"✓";color:var(--pass)}.price.blue-edge li:before{color:var(--blue-ink)}
.faq{display:grid;gap:10px;max-width:860px}.qa{padding:0}.qa summary{cursor:pointer;padding:20px 24px;font:500 19px var(--fd);letter-spacing:-.02em;list-style:none;display:flex;justify-content:space-between}
.qa summary:after{content:"+";color:var(--blue-ink);font-family:var(--fm)}.qa[open] summary:after{content:"–"}.qa p{margin:0;padding:0 24px 22px;color:var(--grey)}
.foot{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;padding:80px 32px 50px;color:var(--grey-2);font-size:14px}.foot p{margin:8px 0 0}
.foot .mono{font-size:12px}
/* results */
#results .wrap,#compare .wrap,#history .wrap{padding-top:28px;padding-bottom:40px}
.rbar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 22px;flex-wrap:wrap}
.rbar h2{font-size:28px;margin:4px 0 0;word-break:break-all}.acts{display:flex;gap:8px;flex-wrap:wrap}
.scores{display:grid;grid-template-columns:1.1fr 1.1fr .9fr .9fr;gap:14px;margin-top:14px}
.sc{padding:20px 22px;position:relative;overflow:hidden}
.gwrap{display:flex;gap:18px;align-items:center;margin-top:10px}
.ring{width:108px;height:108px;flex:none}.ring text{font-family:var(--fd)}
.band{display:inline-block;font:500 11px var(--fm);letter-spacing:.1em;text-transform:uppercase;padding:4px 10px;border-radius:999px;margin-bottom:8px}
.sc p{margin:0;color:var(--grey);font-size:14px}
.delta{font:500 12px var(--fm);margin-left:6px}.up{color:var(--pass)}.down{color:var(--fail)}
.statn{display:flex;gap:20px;margin-top:14px}.statn b{display:block;font:500 34px/1 var(--fd);letter-spacing:-.04em}.statn span{font:400 11px var(--fm);color:var(--grey-2);text-transform:uppercase;letter-spacing:.08em}
.locked-ov{position:absolute;inset:0;background:linear-gradient(180deg,rgba(7,8,11,0),rgba(7,8,11,.55));display:flex;align-items:flex-end;padding:16px 22px;pointer-events:none}
.tabs{display:flex;gap:4px;margin:22px 0 16px;border-bottom:1px solid var(--line);overflow-x:auto}
.tab{background:none;border:0;padding:12px 16px;font:500 12px var(--fm);letter-spacing:.1em;text-transform:uppercase;color:var(--grey-2);cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap}
.tab.on{color:var(--ledger);border-color:var(--blue-ink)}.tab .tag{margin-left:6px;padding:2px 6px}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.grid.g3{grid-template-columns:repeat(3,1fr)}
.area{padding:18px;cursor:pointer;transition:.3s var(--ease);text-align:left;border:1px solid var(--line);width:100%}
.area:hover{border-color:rgba(142,160,255,.35);transform:translateY(-2px)}
.area h4{margin:10px 0 2px;font:500 17px var(--fd);letter-spacing:-.02em}
.area .s{font:500 42px/1 var(--fd);letter-spacing:-.05em;margin:12px 0 10px}.area .s small{font-size:14px;color:var(--grey-2);letter-spacing:0}
.bar2{height:4px;border-radius:4px;background:rgba(244,241,234,.07);overflow:hidden}.bar2 i{display:block;height:100%;border-radius:4px}
.dots{display:flex;gap:3px;margin-top:12px;flex-wrap:wrap}.dots i{width:8px;height:8px;border-radius:2px}
.p{background:var(--pass)}.w{background:var(--warn)}.f{background:var(--fail)}.s0{background:#2b303b}.l{background:var(--lock)}
.km{display:flex;justify-content:space-between;margin-top:12px;font-size:12px;color:var(--grey-2)}.km b{color:var(--ledger);font-weight:500}
.panel2{padding:22px}.panel2 h3{margin-top:0}
.split{display:grid;grid-template-columns:1.4fr 1fr;gap:14px;margin-bottom:14px}
.prio{list-style:none;margin:0;padding:0}.prio li{display:grid;grid-template-columns:28px 1fr;gap:10px;padding:14px 0;border-top:1px solid var(--line)}
.prio .n{font:500 12px var(--fm);color:var(--grey-2);padding-top:2px}.prio b{font-weight:600}.prio p{margin:4px 0 0;color:var(--grey);font-size:14px}.prio .fx{color:var(--ledger)}
.meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.summary{white-space:pre-wrap;color:#d9d6cf;font-size:15.5px;margin:10px 0 0}
.serp{background:#fff;color:#202124;border-radius:12px;padding:16px 18px;font-family:Arial,sans-serif;margin-top:10px}
.serp .u{font-size:13px;color:#4d5156}.serp .t{font-size:19px;color:#1a0dab;margin:4px 0}.serp .d{font-size:14px;color:#4d5156;line-height:1.5}
.kv{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}.kv div{background:rgba(244,241,234,.03);border:1px solid var(--line);border-radius:12px;padding:12px}
.kv b{display:block;font:500 20px var(--fd);margin-top:6px;letter-spacing:-.02em}
table{width:100%;border-collapse:collapse;font-size:14px}th{font:500 10.5px var(--fm);letter-spacing:.1em;text-transform:uppercase;color:var(--grey-2);text-align:left;padding:12px 14px;white-space:nowrap}
td{padding:12px 14px;border-top:1px solid var(--line);vertical-align:top}.tablewrap{overflow-x:auto;padding:4px}
tr.row{cursor:pointer}tr.row:hover td{background:rgba(244,241,234,.03)}
.pill{display:inline-block;min-width:40px;text-align:center;padding:3px 8px;border-radius:8px;font:600 13px var(--fm);color:#07080b}
.st{display:inline-flex;align-items:center;gap:6px;font:500 12px var(--fm)}.st i{width:8px;height:8px;border-radius:50%}
.okc{color:var(--pass)}.bad{color:var(--fail)}.mid{color:var(--warn)}.dim{color:var(--grey-2)}
.techg{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.techg .card{padding:18px}.techg .chips{margin-top:10px}
.techg .chip{color:var(--ledger);border-color:var(--line-2)}
.code{position:relative;margin-top:10px}.code pre{margin:0;background:#05060a;border:1px solid var(--line);border-radius:12px;padding:16px;overflow:auto;max-height:320px;font:12.5px/1.6 var(--fm);color:#cfd5ff}
.code .cbtn{position:absolute;top:8px;right:8px;display:flex;gap:6px}
.fixc{padding:20px;margin-bottom:12px}.fixc p{color:var(--grey);font-size:14px;margin:6px 0 0}
.todo{list-style:none;margin:0;padding:0}.todo li{display:grid;grid-template-columns:24px 1fr auto;gap:12px;padding:14px 0;border-top:1px solid var(--line);align-items:start}
.todo input{width:18px;height:18px;accent-color:var(--blue);margin-top:3px}.todo li.done b,.todo li.done p{text-decoration:line-through;opacity:.45}
.todo p{margin:4px 0 0;color:var(--grey);font-size:14px}
.prog{height:6px;border-radius:6px;background:rgba(244,241,234,.07);overflow:hidden;margin:10px 0 4px}.prog i{display:block;height:100%;background:var(--blue-ink)}
.lock{position:relative}.lock .blur{filter:blur(5px);opacity:.55;pointer-events:none;user-select:none}
.upsell{padding:28px;border-color:rgba(142,160,255,.3);background:linear-gradient(135deg,rgba(35,64,217,.25),rgba(14,17,22,.9) 60%);display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;margin-bottom:14px}
.upsell h3{font-size:28px;margin:6px 0}.upsell p{margin:0;color:var(--grey);max-width:560px}
.sov{font:500 72px/1 var(--fd);letter-spacing:-.06em;color:var(--blue-ink)}
.vq{padding:14px 0;border-top:1px solid var(--line)}.vq summary{cursor:pointer;display:flex;gap:10px;align-items:center;list-style:none}
.vq p{color:var(--grey);font-size:13.5px;margin:8px 0}.vq .src{font:12px var(--fm);color:var(--grey-2);word-break:break-all}
.comp{display:flex;align-items:center;gap:10px;padding:6px 0;font-size:14px}.comp .bar2{flex:1}
textarea,.inp{width:100%;background:#05060a;border:1px solid var(--line-2);border-radius:12px;color:var(--ledger);font:14px/1.5 var(--fb);padding:12px 14px;outline:none}
textarea:focus,.inp:focus{border-color:rgba(142,160,255,.6)}
label.fl{display:block;font:500 11px var(--fm);letter-spacing:.1em;text-transform:uppercase;color:var(--grey);margin:14px 0 6px}
/* drawer & modal */
.drawer,.modal{position:fixed;inset:0;z-index:40;background:rgba(4,5,8,.6);backdrop-filter:blur(4px);display:none}
.drawer.on{display:block}.modal.on{display:grid;place-items:center;padding:14px}
.dpanel{position:absolute;right:14px;top:14px;bottom:14px;width:min(560px,calc(100% - 28px));overflow:auto;padding:26px;animation:slide .45s var(--ease)}
@keyframes slide{from{transform:translateX(30px);opacity:0}to{transform:none;opacity:1}}
.chk{padding:16px 0;border-top:1px solid var(--line)}.chk h5{margin:0;font:500 15px var(--fb);display:flex;gap:10px;align-items:center}
.chk p{margin:6px 0 0;color:var(--grey);font-size:14px}.chk code{display:block;font:12px var(--fm);color:var(--grey-2);margin-top:4px;word-break:break-all}
.chk .fx{color:var(--ledger)}
.mbox{position:relative;width:min(520px,100%);max-height:calc(100vh - 28px);overflow:auto;padding:28px;animation:fade .4s var(--ease)}
.mtabs{display:flex;gap:6px;margin:14px 0 4px}.mtabs button{flex:1}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);background:var(--ledger);color:#0e1116;padding:11px 18px;border-radius:999px;font-weight:600;font-size:14px;opacity:0;transition:.35s var(--ease);z-index:60;pointer-events:none}
.toast.on{opacity:1;transform:translateX(-50%)}
.empty{padding:48px;text-align:center;color:var(--grey-2)}
@media(max-width:1100px){.grid{grid-template-columns:repeat(3,1fr)}.scores{grid-template-columns:1fr 1fr}}
@media(max-width:900px){.hero{grid-template-columns:1fr;min-height:0;padding-top:40px}.hero-r{height:380px}.two,.three,.split,.techg{grid-template-columns:1fr}
.links{display:none}.kv{grid-template-columns:repeat(2,1fr)}.grid,.grid.g3{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.wrap,.nav{padding-left:18px;padding-right:18px}.sec{padding:70px 18px 0}.bar{flex-wrap:wrap;border-radius:20px;padding:10px}.bar .btn{width:100%}
.scores,.grid,.grid.g3{grid-template-columns:1fr}#unlockBtn{display:none}.hero-r{height:340px}.insp{width:100%!important;left:0!important}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media print{body{background:#fff}.nav,.globe,.glow,.foot,.acts,.tabs{display:none}}
"""
