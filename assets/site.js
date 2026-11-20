(function(){
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
// mobile menu
const mb=$(".menu-btn"),mm=$("#mainmenu");
if(mb&&mm){mb.addEventListener("click",()=>{const o=mb.getAttribute("aria-expanded")==="true";mb.setAttribute("aria-expanded",String(!o));mm.classList.toggle("open",!o)})}
// directory filtering (server-rendered cards stay crawlable)
const list=$("#list");
if(list){
  const cards=$$("#list .card"),st={q:"",r:"",c:"",k:"",sec:""};
  const p=new URLSearchParams(location.search);["q","c","k","sec","r"].forEach(k=>{st[k]=p.get(k)||""});
  const q=$("#q"),fr=$("#f-region"),fc=$("#f-country"),fk=$("#f-cat");
  function run(){
    q.value=st.q;fr.value=st.r;fc.value=st.c;fk.value=st.k;
    $$("#filters .chip").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.sec===st.sec)));
    const t=st.q.toLowerCase().split(/\s+/).filter(Boolean);let n=0;
    cards.forEach(c=>{const ok=(!st.r||c.dataset.r===st.r)&&(!st.c||c.dataset.c===st.c)&&(!st.k||c.dataset.k.split("|").includes(st.k))&&(!st.sec||c.dataset.sec.split(" ").includes(st.sec))&&t.every(w=>c.dataset.h.includes(w));c.hidden=!ok;if(ok)n++});
    $("#count").textContent=n+" of "+cards.length+" shown";$("#empty").hidden=n>0;
    const u=new URLSearchParams();["q","c","k","sec","r"].forEach(k=>{if(st[k])u.set(k,st[k])});
    try{history.replaceState(null,"",location.pathname+(u.toString()?"?"+u:""))}catch(e){}
  }
  q.addEventListener("input",()=>{st.q=q.value;run()});
  fr.addEventListener("change",()=>{st.r=fr.value;run()});fc.addEventListener("change",()=>{st.c=fc.value;run()});fk.addEventListener("change",()=>{st.k=fk.value;run()});
  $$("#filters .chip").forEach(b=>b.addEventListener("click",()=>{st.sec=b.dataset.sec;run()}));
  run();
}
// submit and claim forms
const f=$("#sub");
if(f){
  const pn=new URLSearchParams(location.search).get("n");if(pn&&$("#f-name"))$("#f-name").value=pn;
  f.addEventListener("submit",async ev=>{ev.preventDefault();
    const req=$$("#sub [required]").filter(el=>!el.value.trim());
    if(req.length){$("#f-status").textContent="Fill in the fields marked *.";req[0].focus();return}
    const entry={type:f.dataset.mode};
    $$("#sub [id^='f-']").forEach(el=>{const val=el.value.trim();if(val)entry[el.id.slice(2)]=val});
    if(f.dataset.mode==="job"){entry.job_title=entry.name;delete entry.name}
    if(f.dataset.endpoint){try{const r=await fetch(f.dataset.endpoint,{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(entry)});if(r.ok){$("#f-status").textContent="Received. We will check the details and reply by email.";f.reset();return}}catch(e){}}
    const text=Object.entries(entry).map(([k,x])=>k+": "+x).join("\n");
    $("#out-text").textContent=text;$("#out").hidden=false;
    $("#mail").href="mailto:"+f.dataset.email+"?subject="+encodeURIComponent(({claim:"Claim profile: ",job:"Job post: "}[f.dataset.mode]||"New listing: ")+(entry.name||entry.job_title))+"&body="+encodeURIComponent(text);
    $("#f-status").textContent="Ready. Open the email (or copy the text) and send it to "+f.dataset.email+".";
  });
  $("#copy").addEventListener("click",()=>{const t=$("#out-text").textContent;navigator.clipboard.writeText(t).then(()=>{$("#copy").textContent="Copied"},()=>{const r=document.createRange();r.selectNodeContents($("#out-text"));const s=getSelection();s.removeAllRanges();s.addRange(r)})});
}
})();
