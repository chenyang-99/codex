export const FILM={
 fig:"Fig 1",title:"60% mechanical keyboard",radius:235,
 label:"An independently modeled simplified 61-key keyboard rotating, with close-ups of keycaps, a spacebar press, exploded electronics and reassembly.",
 bounds:[[-148,148],[-58,58],[-6,145]]
};
export const FIGURE={
 title:"Mechanical keyboard · anatomy",start:{yaw:-33,pitch:32},
 label:"An original simplified 60% keyboard with {parts} convex parts: 61 labelled keycaps, 61 switches, separate mounting plate, printed circuit board and outer case. The exploded figure has {assemblies} movable groups. Dimensions are assumed, not manufacturer-verified.",
 keys:[
  {mark:"raised",label:"Keycaps: 61 individually removable solids"},
  {mark:"lit",label:"Switches: 61 simplified housings"},
  {mark:"edge",label:"Structure: plate, PCB, case, feet, connector"}
 ],
 caption:"Independent new-object geometry, not reused espresso model. This is an illustration, not a repair diagram. Drag to rotate, hover/A to explode, P to press the spacebar."
};
export const FEATURE_DEFAULTS={press:0};
export const FEATURE_KEYS=[{key:"p",channel:"press",name:"spacebar press",unit:"mm",values:[0,1],ease:0.2,verb:"presses the spacebar"}];
export function featureValues(s,values){return {...values,"space.press":(s.press??0)*1.4};}
export function featureTravel(a,b){return Math.abs((b.press??0)-(a.press??0))*1.4;}
