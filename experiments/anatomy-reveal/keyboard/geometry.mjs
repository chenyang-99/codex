// New-object test: independent 60% keyboard geometry for Anatomy Reveal.
const F={o:[0,0,0],a:[0,0,1],u:[1,0,0],v:[0,1,0]};
const Z=[0,0,1];
export function buildObject(T,{layer}){
 const parts={},groups={},explode=[],anchors={},features=[];
 const root=T.group("root",{free:{origin:[0,0,16]}});
 groups.root=root;
 function assembly(name,travel,delay){
   const g=T.group(name,{parent:root,slide:{direction:Z,travel}});
   groups[name]=g;explode.push({name,travel,delay});return g;
 }
 function box(name,group,x0,x1,y0,y1,z0,z1,material="steel"){
   const p=T.prism({name,group,layer,F,polygon:[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],s0:z0,s1:z1,steps:5,tone:"hi",crease:"lo",bevel:0,material});
   parts[name]=p;return p;
 }
 const shell=T.group("case",{parent:root,slide:{direction:Z,travel:0}});groups.case=shell;
 box("case.bottom",shell,-145,145,-53,53,0,6,"gunmetal");
 box("case.left",shell,-145,-138,-53,53,6,28,"gunmetal");
 box("case.right",shell,138,145,-53,53,6,28,"gunmetal");
 box("case.back",shell,-138,138,-53,-46,6,28,"gunmetal");
 box("case.front",shell,-138,138,46,53,6,28,"gunmetal");
 for(const [i,x,y] of [[0,-113,-35],[1,113,-35],[2,-113,35],[3,113,35]])box("foot."+i,shell,x-12,x+12,y-7,y+7,-4,0,"rubber");
 box("connector.usb",shell,-7,7,-57,-53,15,20,"steel");
 const pcb=assembly("pcb",31,0.39);
 box("pcb.substrate",pcb,-135,135,-43,43,8,10,"pcb");
 const plate=assembly("mounting.plate",58,0.26);
 // Intentionally a solid simplified plate, not an engineering cutout model.
 box("mounting.plate.top",plate,-136,136,-45.7,45.7,13,15,"steel");
 const switches=assembly("switches",80,0.11);
 const rows=[
  ["Esc","1","2","3","4","5","6","7","8","9","0","-","=","Back"],
  ["Tab","Q","W","E","R","T","Y","U","I","O","P","[","]","Bsl"],
  ["Caps","A","S","D","F","G","H","J","K","L",";","'","Enter"],
  ["Shift","Z","X","C","V","B","N","M",",",".","/","Shift"],
  ["Ctrl","Win","Alt","Space","Alt","Fn","Menu","Ctrl"]
 ];
 function legend(part,x,y,z,label){
  const safe=label.replaceAll("&","&amp;").replaceAll("<","&lt;");
  const sz=label.length>4?5.5:label.length>3?6.2:8;
  const svg='<text class="iso-face-text" data-tone="lo" font-size="'+sz+'" text-anchor="middle" font-family="Arial,sans-serif" transform="translate(0 2)">'+safe+'</text>';
  T.plane({part,o:[x,y,z+0.02],u:[1,0,0],v:[0,1,0],normal:Z,svg,fade:[0.04,0.3]});
 }
 let keys=0;
 for(let row=0;row<rows.length;row++){
  const labels=rows[row], y=-38+row*19;
  const spans=row===4?[1.25,1.25,1.25,5,1.25,1.25,1.25,1.25]:labels.map(()=>1);
  const pitch=row===4?19:labels.length===14?19:labels.length===13?20.5:22.3;
  const width=spans.reduce((a,b)=>a+b,0)*pitch;
  let cursor=-width/2;
  labels.forEach((label,i)=>{
   const w=spans[i]*pitch,x=cursor+w/2;cursor+=w;
   const name="key."+row+"."+i;
   const capG=assembly("cap."+row+"."+i,108,0);
   const g=label==="Space"?T.group("space.press",{parent:capG,slide:{direction:[0,0,-1],travel:1.4}}):capG;
   if(label==="Space"){groups["space.press"]=g;anchors.space=[x,y,32];}
   const mod=/^(Esc|Tab|Caps|Shift|Ctrl|Win|Alt|Fn|Menu|Enter|Back|Space)$/.test(label);
   const cap=box(name+".cap",g,x-w/2+1.4,x+w/2-1.4,y-7.6,y+7.6,24.5,32,mod?"lavender":"porcelain");
   legend(cap,x,y,32,label);
   box(name+".switch",switches,x-4,x+4,y-4,y+4,16.6,22.8,"gunmetal");
   keys++;
   if(row===0&&i===0)anchors.escape=[x,y,32];
   if(row===2&&i===4)anchors.home=[x,y,32];
  });
 }
 anchors.body=[0,0,16];anchors.plate=[0,0,15];anchors.pcb=[0,0,9];anchors.usb=[0,-55,18];anchors.switches=[0,0,20];
 for(let n=0;n<=4;n++)features.push({"space.press":n*0.35});
 return {parts,groups,explode,root,anchors,features,counts:{keys}};
}
export function explodeValues(explode,apart,{stretch=0.55}={}){
 const out={};
 for(const {name,travel,delay} of explode){
  const t=Math.max(0,Math.min(1,(apart-delay*stretch)/(1-stretch)));
  out[name]=travel*t*t*(3-2*t);
 }
 return out;
}
