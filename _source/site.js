(function(){
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
// Directory filtering (works on the server-rendered cards, so every listing is crawlable)
const list=$("#list");
if(list){
  const cards=$$("#list .card"),st={q:"",r:"",c:"",s:"",k:""};
  const p=new URLSearchParams(location.search);st.q=p.get("q")||"";st.s=p.get("s")||"";st.c=p.get("c")||"";st.k=p.get("k")||"";
  const q=$("#q"),fr=$("#f-region"),fc=$("#f-country"),fs=$("#f-service");
  function run(){
    q.value=st.q;fr.value=st.r;fc.value=st.c;fs.value=st.s;
    $$(".chips .chip").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.k===st.k)));
    const t=st.q.toLowerCase().split(/\s+/).filter(Boolean);let n=0;
    cards.forEach(c=>{const ok=(!st.r||c.dataset.r===st.r)&&(!st.c||c.dataset.c===st.c)&&(!st.k||c.dataset.k===st.k)&&(!st.s||c.dataset.s.split("|").includes(st.s))&&t.every(w=>c.dataset.h.includes(w));c.hidden=!ok;if(ok)n++});
    $("#count").textContent=n+" of "+cards.length+" shown";$("#empty").hidden=n>0;
    const u=new URLSearchParams();if(st.q)u.set("q",st.q);if(st.s)u.set("s",st.s);if(st.c)u.set("c",st.c);if(st.k)u.set("k",st.k);
    try{history.replaceState(null,"",location.pathname+(u.toString()?"?"+u:""))}catch(e){}
  }
  q.addEventListener("input",()=>{st.q=q.value;run()});
  fr.addEventListener("change",()=>{st.r=fr.value;run()});fc.addEventListener("change",()=>{st.c=fc.value;run()});fs.addEventListener("change",()=>{st.s=fs.value;run()});
  $$(".chips .chip").forEach(b=>b.addEventListener("click",()=>{st.k=b.dataset.k;run()}));
  run();
}
// Submission form
const f=$("#sub");
if(f){
  f.addEventListener("submit",async ev=>{ev.preventDefault();
    const v=id=>$("#f-"+id).value.trim();
    if(!v("name")||!v("country")){$("#f-status").textContent="Add at least the company name and country.";return}
    const entry={name:v("name"),category:v("cat"),country:v("country"),city:v("city"),services:v("services").split(",").map(s=>s.trim()).filter(Boolean).join("; "),website:v("web"),phone:v("phone"),email:v("email"),description:v("desc"),source:"Self-submitted (check)"};
    if(f.dataset.endpoint){try{const r=await fetch(f.dataset.endpoint,{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(entry)});if(r.ok){$("#f-status").textContent="Received. We will check the details and publish your listing.";f.reset();return}}catch(e){}}
    $("#out-text").textContent=Object.entries(entry).map(([k,x])=>k+": "+(x||"–")).join("\n");$("#out").hidden=false;
    $("#f-status").textContent="Your listing is ready below. Copy it and email it to "+f.dataset.email+".";
  });
  $("#copy").addEventListener("click",()=>{const t=$("#out-text").textContent;navigator.clipboard.writeText(t).then(()=>{$("#copy").textContent="Copied"},()=>{const r=document.createRange();r.selectNodeContents($("#out-text"));const s=getSelection();s.removeAllRanges();s.addRange(r)})});
}
})();
